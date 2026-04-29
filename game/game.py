from game.deck import Deck
from game.card import Card


class Game:
    def __init__(self, players):
        self.players = players
        self.deck = Deck()
        self.discard_pile = []
        self.direction = 1  # 1=clockwise, -1=counter
        self.current_index = 0
        self.top_color = None
        self._deal()
        self._init_discard()

    def _deal(self):
        for player in self.players:
            player.add_cards(self.deck.draw_multiple(7))

    def _init_discard(self):
        while True:
            card = self.deck.draw()
            if card.card_type != "Wild Draw Four":
                self.discard_pile.append(card)
                self.top_color = card.color
                if card.is_wild():
                    self.top_color = "Red"
                break
            self.deck.cards.insert(0, card)
            self.deck.shuffle()

    @property
    def top_card(self):
        return self.discard_pile[-1]

    @property
    def effective_top(self):
        card = self.top_card
        if card.is_wild():
            # Return a virtual card with chosen color for matching
            return Card(self.top_color, card.card_type)
        return card

    @property
    def current_player(self):
        return self.players[self.current_index]

    def next_player_index(self):
        return (self.current_index + self.direction) % len(self.players)

    def advance_turn(self):
        self.current_index = (self.current_index + self.direction) % len(self.players)

    def play_card(self, card):
        self.discard_pile.append(card)
        if not card.is_wild():
            self.top_color = card.color

    def apply_action(self, card, choose_color_fn):
        if card.card_type == "Reverse":
            self.direction *= -1
            if len(self.players) == 2:
                self.advance_turn()
        elif card.card_type == "Skip":
            self.advance_turn()
        elif card.card_type == "Draw Two":
            next_idx = self.next_player_index()
            drawn = self.deck.draw_multiple(2)
            self.players[next_idx].add_cards(drawn)
            self.advance_turn()
        elif card.card_type == "Wild":
            self.top_color = choose_color_fn()
        elif card.card_type == "Wild Draw Four":
            self.top_color = choose_color_fn()
            next_idx = self.next_player_index()
            drawn = self.deck.draw_multiple(4)
            self.players[next_idx].add_cards(drawn)
            self.advance_turn()

    def draw_card(self, player):
        card = self.deck.draw()
        if card:
            player.hand.append(card)
        return card
