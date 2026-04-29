from game.game import Game
from game.player import Player
from ui.terminal_ui import TerminalUI


def get_setup():
    print("=" * 40)
    print("       🃏 UNO CARD GAME 🃏")
    print("=" * 40)
    name = input("\nEnter your name: ").strip() or "Player"
    while True:
        try:
            num = int(input("Number of AI opponents (1-3): "))
            if 1 <= num <= 3:
                break
        except ValueError:
            pass
        print("Enter 1, 2, or 3.")
    players = [Player(name)]
    for i in range(num):
        players.append(Player(f"Bot {i + 1}", is_ai=True))
    return players


def play_turn(game, ui):
    player = game.current_player
    ui.show_top_card(game)
    ui.show_player_info(game.players, player)

    if player.is_ai:
        idx = player.ai_choose(game.effective_top)
        if idx is not None:
            card = player.play_card(idx)
            ui.announce_ai_play(player, card)
            game.play_card(card)

            def color_fn():
                c = player.ai_choose_color()
                ui.announce_ai_color(player, c)
                return c

            game.apply_action(card, color_fn)
        else:
            ui.announce_ai_draw(player)
            drawn = game.draw_card(player)
            if drawn and drawn.matches(game.effective_top):
                player.hand.remove(drawn)
                ui.announce_ai_play(player, drawn)
                game.play_card(drawn)
                game.apply_action(drawn, lambda: player.ai_choose_color())
    else:
        ui.show_hand(player)
        idx = ui.get_player_choice(player, game)
        if idx is not None:
            card = player.play_card(idx)
            game.play_card(card)
            game.apply_action(card, ui.choose_color)
        else:
            drawn = game.draw_card(player)
            ui.announce_draw(player, drawn)
            if drawn and drawn.matches(game.effective_top):
                play_drawn = input(f"You drew {drawn}. Play it? (y/n): ").lower()
                if play_drawn == "y":
                    player.hand.remove(drawn)
                    game.play_card(drawn)
                    if drawn.is_wild():
                        game.apply_action(drawn, ui.choose_color)
                    else:
                        game.apply_action(drawn, None)

    if player.has_uno():
        ui.announce_uno(player)

    if player.has_won():
        return player
    game.advance_turn()
    return None


def main():
    players = get_setup()
    game = Game(players)
    ui = TerminalUI()

    print("\n🎮 Game Start!\n")
    winner = None
    while not winner:
        winner = play_turn(game, ui)

    ui.announce_winner(winner)


if __name__ == "__main__":
    main()
