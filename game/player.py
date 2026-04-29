import random
from game.card import Card


class Player:
    def __init__(self, name, is_ai=False):
        self.name = name
        self.is_ai = is_ai
        self.hand = []

    def playable_cards(self, top_card):
        return [c for c in self.hand if c.matches(top_card)]

    def play_card(self, index):
        return self.hand.pop(index)

    def add_cards(self, cards):
        self.hand.extend(cards)

    def has_uno(self):
        return len(self.hand) == 1

    def has_won(self):
        return len(self.hand) == 0

    def ai_choose(self, top_card):
        playable = self.playable_cards(top_card)
        if not playable:
            return None
        chosen = random.choice(playable)
        return self.hand.index(chosen)

    def ai_choose_color(self):
        colors = [c.color for c in self.hand if c.color]
        if colors:
            return max(set(colors), key=colors.count)
        return random.choice(Card.COLORS)
