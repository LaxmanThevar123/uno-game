from game.card import Card


class TerminalUI:
    @staticmethod
    def show_top_card(game):
        top = game.top_card
        color_info = f" (Color: {game.top_color})" if top.is_wild() else ""
        print(f"\n--- Top Card: {top}{color_info} ---")

    @staticmethod
    def show_hand(player):
        print(f"\n{player.name}'s Hand:")
        for i, card in enumerate(player.hand):
            print(f"  {i + 1}. {card}")

    @staticmethod
    def show_player_info(players, current):
        print("\nPlayers:")
        for p in players:
            marker = " <--" if p == current else ""
            print(f"  {p.name}: {len(p.hand)} cards{marker}")

    @staticmethod
    def get_player_choice(player, game):
        playable = player.playable_cards(game.effective_top)
        if not playable:
            input(f"\n{player.name} has no valid card. Press Enter to draw...")
            return None

        while True:
            try:
                choice = input(f"\nChoose card (1-{len(player.hand)}) or 0 to draw: ")
                idx = int(choice) - 1
                if idx == -1:
                    return None
                if 0 <= idx < len(player.hand):
                    card = player.hand[idx]
                    if card.matches(game.effective_top):
                        return idx
                    print("That card can't be played!")
                else:
                    print("Invalid number.")
            except ValueError:
                print("Enter a number.")

    @staticmethod
    def choose_color():
        print("\nChoose color:")
        for i, color in enumerate(Card.COLORS, 1):
            print(f"  {i}. {color}")
        while True:
            try:
                choice = int(input("Color (1-4): "))
                if 1 <= choice <= 4:
                    return Card.COLORS[choice - 1]
            except ValueError:
                pass
            print("Invalid choice.")

    @staticmethod
    def announce_uno(player):
        print(f"\n🎉 UNO! {player.name} has one card left!")

    @staticmethod
    def announce_winner(player):
        print(f"\n🏆 {player.name} WINS! Congratulations! 🏆")

    @staticmethod
    def announce_draw(player, card):
        if card:
            print(f"{player.name} drew a card.")
        else:
            print("Deck is empty!")

    @staticmethod
    def announce_ai_play(player, card):
        print(f"\n{player.name} plays {card}")

    @staticmethod
    def announce_ai_draw(player):
        print(f"{player.name} draws a card.")

    @staticmethod
    def announce_ai_color(player, color):
        print(f"{player.name} chooses {color}")
