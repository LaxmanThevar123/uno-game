import streamlit as st
from game.game import Game
from game.player import Player
from game.card import Card

st.set_page_config(page_title="UNO", page_icon="🃏", layout="centered")

# Mobile-friendly CSS
st.markdown("""
<style>
    .stApp { max-width: 600px; margin: auto; }
    .card-btn button { font-size: 1.1rem !important; padding: 0.5rem !important; width: 100% !important; }
    .top-card { font-size: 2rem; text-align: center; padding: 1rem;
        border-radius: 12px; margin: 1rem 0; color: white; font-weight: bold; }
    .red { background: #d32f2f; } .blue { background: #1565c0; }
    .green { background: #2e7d32; } .yellow { background: #f9a825; color: #333; }
    .wild { background: #333; }
    .player-info { padding: 0.3rem 0; font-size: 0.95rem; }
    .uno-alert { font-size: 1.5rem; text-align: center; padding: 0.5rem; }
</style>
""", unsafe_allow_html=True)


def get_card_color_class(card):
    if card.is_wild():
        return "wild"
    return card.color.lower()


def card_label(card):
    if card.is_wild():
        return f"🌈 {card.card_type}"
    emoji = {"Red": "🔴", "Blue": "🔵", "Green": "🟢", "Yellow": "🟡"}
    return f"{emoji.get(card.color, '')} {card.card_type}"


def init_game(player_name, num_bots):
    players = [Player(player_name)]
    for i in range(num_bots):
        players.append(Player(f"Bot {i+1}", is_ai=True))
    st.session_state.game = Game(players)
    st.session_state.message = "Your turn! Play a card."
    st.session_state.choosing_color = False
    st.session_state.pending_card = None
    st.session_state.game_over = False


def ai_turns():
    game = st.session_state.game
    messages = []
    while game.current_player.is_ai and not st.session_state.game_over:
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
                messages.append(f"🤖 {player.name} plays {card_label(card)} → {color}")
            else:
                game.apply_action(card, None)
                messages.append(f"🤖 {player.name} plays {card_label(card)}")
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
                messages.append(f"🤖 {player.name} draws and plays {card_label(drawn)}")
            else:
                messages.append(f"🤖 {player.name} draws a card")

        if player.has_uno():
            messages.append(f"🎉 {player.name} says UNO!")
        if player.has_won():
            st.session_state.game_over = True
            st.session_state.message = f"🤖 {player.name} wins! Better luck next time."
            return "\n\n".join(messages)
        game.advance_turn()

    st.session_state.message = "Your turn! Play a card."
    return "\n\n".join(messages)


# --- SETUP SCREEN ---
if "game" not in st.session_state:
    st.markdown("# 🃏 UNO")
    name = st.text_input("Your name", value="Player")
    bots = st.selectbox("Number of opponents", [1, 2, 3], index=0)
    if st.button("▶️ Start Game", use_container_width=True):
        init_game(name or "Player", bots)
        st.rerun()
    st.stop()

game = st.session_state.game
human = game.players[0]

# --- COLOR CHOOSER ---
if st.session_state.choosing_color:
    st.markdown("### Choose a color:")
    cols = st.columns(4)
    for i, color in enumerate(Card.COLORS):
        emoji = {"Red": "🔴", "Blue": "🔵", "Green": "🟢", "Yellow": "🟡"}
        if cols[i].button(f"{emoji[color]}", key=f"color_{color}", use_container_width=True):
            game.top_color = color
            card = st.session_state.pending_card
            if card.card_type == "Wild Draw Four":
                nxt = game.next_player_index()
                game.players[nxt].add_cards(game.deck.draw_multiple(4))
                game.advance_turn()
            st.session_state.choosing_color = False
            st.session_state.pending_card = None
            if human.has_uno():
                st.session_state.message = "🎉 UNO!"
            if human.has_won():
                st.session_state.game_over = True
                st.session_state.message = "🏆 You WIN! Congratulations!"
            else:
                game.advance_turn()
                ai_log = ai_turns()
                if ai_log:
                    st.session_state.ai_log = ai_log
            st.rerun()
    st.stop()

# --- GAME OVER ---
if st.session_state.game_over:
    st.markdown(f"## {st.session_state.message}")
    if st.button("🔄 Play Again", use_container_width=True):
        del st.session_state.game
        st.rerun()
    st.stop()

# --- GAME BOARD ---
st.markdown("## 🃏 UNO")

# Player info
for p in game.players:
    marker = " 👈" if p == game.current_player else ""
    st.markdown(f"<div class='player-info'>{'🧑' if not p.is_ai else '🤖'} {p.name}: **{len(p.hand)}** cards{marker}</div>", unsafe_allow_html=True)

# Top card
top = game.top_card
color_class = get_card_color_class(top)
display_color = game.top_color if top.is_wild() else top.color
st.markdown(f"<div class='top-card {color_class}'>{card_label(top)}<br><small>{display_color}</small></div>", unsafe_allow_html=True)

# Status message
st.info(st.session_state.message)

# AI log
if "ai_log" in st.session_state and st.session_state.ai_log:
    with st.expander("🤖 Bot actions", expanded=True):
        st.markdown(st.session_state.ai_log)

# Hand
st.markdown(f"**Your hand ({len(human.hand)} cards):**")
playable = human.playable_cards(game.effective_top)

cols_per_row = 3
for row_start in range(0, len(human.hand), cols_per_row):
    cols = st.columns(cols_per_row)
    for i, col in enumerate(cols):
        idx = row_start + i
        if idx >= len(human.hand):
            break
        card = human.hand[idx]
        can_play = card in playable
        label = card_label(card)
        if col.button(label, key=f"card_{idx}", disabled=not can_play, use_container_width=True):
            played = human.play_card(idx)
            game.play_card(played)
            if played.is_wild():
                st.session_state.choosing_color = True
                st.session_state.pending_card = played
            else:
                game.apply_action(played, None)
                if human.has_uno():
                    st.session_state.message = "🎉 UNO!"
                if human.has_won():
                    st.session_state.game_over = True
                    st.session_state.message = "🏆 You WIN! Congratulations!"
                else:
                    game.advance_turn()
                    ai_log = ai_turns()
                    if ai_log:
                        st.session_state.ai_log = ai_log
            st.rerun()

# Draw button
st.markdown("---")
if not playable:
    if st.button("📥 Draw a Card", use_container_width=True):
        drawn = game.draw_card(human)
        if drawn and drawn.matches(game.effective_top):
            st.session_state.message = f"You drew {card_label(drawn)} — it's playable!"
        else:
            st.session_state.message = f"You drew a card. No match."
            game.advance_turn()
            ai_log = ai_turns()
            if ai_log:
                st.session_state.ai_log = ai_log
        st.rerun()
else:
    st.caption("Select a card to play ☝️")

# New game
st.markdown("---")
if st.button("🔄 New Game", use_container_width=True):
    del st.session_state.game
    st.rerun()
