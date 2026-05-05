from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from game.game import Game
from game.player import Player
from game.card import Card
import secrets
import string

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# rooms[code] = { "host": sid, "players": [{sid, name}], "bots": int, "game": Game, "started": bool }
rooms = {}


def generate_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


def card_to_dict(card):
    return {"color": card.color or "Wild", "type": str(card.card_type), "label": f"{card.color or ''} {card.card_type}".strip()}


def get_player_state(room_code, player_name):
    room = rooms[room_code]
    game = room["game"]
    player = next((p for p in game.players if p.name == player_name), None)
    eliminated = player_name in room.get("finished", [])

    playable = []
    if player and not eliminated and game.current_player == player:
        playable = player.playable_cards(game.effective_top)

    hand = []
    if player:
        for c in player.hand:
            d = card_to_dict(c)
            d["playable"] = c in playable
            hand.append(d)

    # Build circular seating order relative to this player
    all_players = game.players
    my_idx = next((i for i, p in enumerate(all_players) if p.name == player_name), 0)
    seating = []
    for i in range(len(all_players)):
        idx = (my_idx + i) % len(all_players)
        p = all_players[idx]
        seating.append({
            "name": p.name,
            "cards": len(p.hand),
            "is_ai": p.is_ai,
            "is_current": p == game.current_player,
            "is_you": p.name == player_name,
            "finished": p.name in room.get("finished", [])
        })

    top = game.top_card
    top_dict = card_to_dict(top)
    top_dict["effective_color"] = game.top_color

    return {
        "hand": hand,
        "top_card": top_dict,
        "seating": seating,
        "current_player": game.current_player.name,
        "is_your_turn": not eliminated and game.current_player.name == player_name,
        "direction": game.direction,
        "deck_count": len(game.deck.cards),
        "player_name": player_name,
        "game_over": False,
        "winner": None,
        "finished": room.get("finished", [])
    }


def broadcast_state(room_code, messages=None, winner=None):
    room = rooms[room_code]
    game = room["game"]
    for p_info in room["players"]:
        state = get_player_state(room_code, p_info["name"])
        if messages:
            state["messages"] = messages
        if winner:
            state["game_over"] = True
            state["winner"] = winner
        socketio.emit("game_state", state, to=p_info["sid"])


def check_winner(room_code, player, messages):
    """When a player empties their hand, they become a watcher.
    Game ends when only 1 active player remains."""
    room = rooms[room_code]
    game = room["game"]
    room["finished"].append(player.name)
    rank = len(room["finished"])
    messages.append(f"🏆 {player.name} finishes #{rank}! Now watching.")

    active_players = [p for p in game.players if p.name not in room["finished"]]

    if len(active_players) <= 1:
        return room["finished"][0]

    # Advance turn past finished players
    game.advance_turn()
    while game.current_player.name in room["finished"]:
        game.advance_turn()
    return None


def run_ai_turns(room_code):
    room = rooms[room_code]
    game = room["game"]
    messages = []

    # Skip finished players
    while game.current_player.name in room.get("finished", []):
        game.advance_turn()

    while game.current_player.is_ai and game.current_player.name not in room.get("finished", []):
        player = game.current_player
        idx = player.ai_choose(game.effective_top)
        if idx is not None:
            card = player.play_card(idx)
            game.play_card(card)
            if card.is_wild():
                color = player.ai_choose_color()
                game.top_color = color
                if card.card_type == "Wild Draw Four":
                    nxt = game.next_player_index()
                    game.players[nxt].add_cards(game.deck.draw_multiple(4))
                    game.advance_turn()
                messages.append(f"🤖 {player.name} plays {card.card_type} → {color}")
            else:
                game.apply_action(card, None)
                messages.append(f"🤖 {player.name} plays {card.color} {card.card_type}")
        else:
            drawn = game.draw_card(player)
            if drawn and drawn.matches(game.effective_top):
                player.hand.remove(drawn)
                game.play_card(drawn)
                if drawn.is_wild():
                    color = player.ai_choose_color()
                    game.top_color = color
                    if drawn.card_type == "Wild Draw Four":
                        nxt = game.next_player_index()
                        game.players[nxt].add_cards(game.deck.draw_multiple(4))
                        game.advance_turn()
                else:
                    game.apply_action(drawn, None)
                messages.append(f"🤖 {player.name} draws & plays")
            else:
                messages.append(f"🤖 {player.name} draws a card")

        if player.has_uno():
            messages.append(f"🎉 {player.name} says UNO!")
        if player.has_won():
            winner = check_winner(room_code, player, messages)
            if winner:
                return messages, winner
            # Skip finished players for next iteration
            while game.current_player.name in room.get("finished", []):
                game.advance_turn()
            continue

        game.advance_turn()
        # Skip finished players
        while game.current_player.name in room.get("finished", []):
            game.advance_turn()

    return messages, None


@app.route("/")
def index():
    return render_template("index.html")


@socketio.on("create_room")
def handle_create(data):
    code = generate_code()
    name = data.get("name", "Host")
    rooms[code] = {
        "host": request.sid,
        "players": [{"sid": request.sid, "name": name}],
        "bots": 0,
        "game": None,
        "started": False
    }
    join_room(code)
    emit("room_created", {"code": code, "players": [name]})


@socketio.on("join_room")
def handle_join(data):
    code = data.get("code", "").upper()
    name = data.get("name", "Player")

    if code not in rooms:
        emit("error", {"msg": "Room not found!"})
        return
    room = rooms[code]
    if room["started"]:
        emit("error", {"msg": "Game already started!"})
        return
    if len(room["players"]) >= 4:
        emit("error", {"msg": "Room is full!"})
        return
    # Check duplicate name
    existing_names = [p["name"] for p in room["players"]]
    if name in existing_names:
        name = f"{name}_{len(room['players'])}"

    room["players"].append({"sid": request.sid, "name": name})
    join_room(code)

    player_names = [p["name"] for p in room["players"]]
    socketio.emit("room_update", {"players": player_names, "code": code}, to=code)


@socketio.on("add_bot")
def handle_add_bot(data):
    code = data.get("code")
    if code not in rooms:
        return
    room = rooms[code]
    if request.sid != room["host"]:
        return
    total = len(room["players"]) + room["bots"]
    if total >= 4:
        emit("error", {"msg": "Max 4 players!"})
        return
    room["bots"] += 1
    player_names = [p["name"] for p in room["players"]] + [f"Bot {i+1}" for i in range(room["bots"])]
    socketio.emit("room_update", {"players": player_names, "code": code}, to=code)


@socketio.on("remove_bot")
def handle_remove_bot(data):
    code = data.get("code")
    if code not in rooms:
        return
    room = rooms[code]
    if request.sid != room["host"]:
        return
    if room["bots"] > 0:
        room["bots"] -= 1
    player_names = [p["name"] for p in room["players"]] + [f"Bot {i+1}" for i in range(room["bots"])]
    socketio.emit("room_update", {"players": player_names, "code": code}, to=code)


@socketio.on("start_game")
def handle_start(data):
    code = data.get("code")
    if code not in rooms:
        return
    room = rooms[code]
    if request.sid != room["host"]:
        return
    if len(room["players"]) + room["bots"] < 2:
        emit("error", {"msg": "Need at least 2 players!"})
        return

    players = [Player(p["name"]) for p in room["players"]]
    for i in range(room["bots"]):
        players.append(Player(f"Bot {i+1}", is_ai=True))

    room["game"] = Game(players)
    room["started"] = True
    room["finished"] = []  # Track players who finished
    room["total_players"] = len(players)

    # Run AI if first turn is bot
    messages, winner = run_ai_turns(code)
    broadcast_state(code, messages, winner)
    socketio.emit("game_started", {}, to=code)


@socketio.on("play_card")
def handle_play(data):
    code = data.get("code")
    card_idx = data.get("card_index")
    chosen_color = data.get("color")

    if code not in rooms:
        return
    room = rooms[code]
    game = room["game"]

    # Find player by sid
    p_info = next((p for p in room["players"] if p["sid"] == request.sid), None)
    if not p_info:
        return
    player = next(p for p in game.players if p.name == p_info["name"])

    if game.current_player != player:
        emit("error", {"msg": "Not your turn!"})
        return

    card = player.hand[card_idx]
    if not card.matches(game.effective_top):
        emit("error", {"msg": "Invalid move!"})
        return

    messages = []
    played = player.play_card(card_idx)
    game.play_card(played)

    if played.is_wild():
        game.top_color = chosen_color or "Red"
        if played.card_type == "Wild Draw Four":
            nxt = game.next_player_index()
            game.players[nxt].add_cards(game.deck.draw_multiple(4))
            messages.append(f"{game.players[nxt].name} draws 4 cards!")
            game.advance_turn()
        messages.append(f"{player.name} plays {played.card_type} → {chosen_color}")
    else:
        if played.card_type == "Skip":
            messages.append(f"{player.name} plays Skip!")
        elif played.card_type == "Draw Two":
            messages.append(f"{player.name} plays Draw Two!")
        elif played.card_type == "Reverse":
            messages.append(f"{player.name} plays Reverse!")
        else:
            messages.append(f"{player.name} plays {played.color} {played.card_type}")
        game.apply_action(played, None)

    if player.has_uno():
        messages.append(f"🎉 {player.name} says UNO!")
    if player.has_won():
        winner = check_winner(code, player, messages)
        if winner:
            broadcast_state(code, messages, winner)
        else:
            game.advance_turn()
            ai_msgs, ai_winner = run_ai_turns(code)
            messages.extend(ai_msgs)
            broadcast_state(code, messages, ai_winner)
        return

    game.advance_turn()
    ai_msgs, winner = run_ai_turns(code)
    messages.extend(ai_msgs)
    broadcast_state(code, messages, winner)


@socketio.on("draw_card")
def handle_draw(data):
    code = data.get("code")
    if code not in rooms:
        return
    room = rooms[code]
    game = room["game"]

    p_info = next((p for p in room["players"] if p["sid"] == request.sid), None)
    if not p_info:
        return
    player = next(p for p in game.players if p.name == p_info["name"])

    if game.current_player != player:
        emit("error", {"msg": "Not your turn!"})
        return

    messages = []
    drawn = game.draw_card(player)

    if drawn and drawn.matches(game.effective_top):
        messages.append(f"{player.name} draws a playable card!")
        # Let them play it on next action — refresh state showing it's playable
        broadcast_state(code, messages)
        return

    messages.append(f"{player.name} draws a card.")
    game.advance_turn()
    ai_msgs, winner = run_ai_turns(code)
    messages.extend(ai_msgs)
    broadcast_state(code, messages, winner)


@socketio.on("chat_message")
def handle_chat(data):
    code = data.get("code")
    msg = data.get("message", "").strip()
    if not code or not msg or code not in rooms:
        return
    p_info = next((p for p in rooms[code]["players"] if p["sid"] == request.sid), None)
    if not p_info:
        return
    socketio.emit("chat_message", {"name": p_info["name"], "message": msg}, to=code)


@socketio.on("disconnect")
def handle_disconnect():
    for code, room in list(rooms.items()):
        room["players"] = [p for p in room["players"] if p["sid"] != request.sid]
        if not room["players"]:
            del rooms[code]
        else:
            if room["host"] == request.sid:
                room["host"] = room["players"][0]["sid"]
            if not room["started"]:
                player_names = [p["name"] for p in room["players"]] + [f"Bot {i+1}" for i in range(room["bots"])]
                socketio.emit("room_update", {"players": player_names, "code": code}, to=code)


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
