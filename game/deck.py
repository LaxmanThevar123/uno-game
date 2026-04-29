import random
from game.card import Card


class Deck:
    def __init__(self):
        self.cards = []
        self._build()
        self.shuffle()

    def _build(self):
        for color in Card.COLORS:
            self.cards.append(Card(color, 0))
            for n in range(1, 10):
                self.cards.append(Card(color, n))
                self.cards.append(Card(color, n))
            for action in ["Skip", "Reverse", "Draw Two"]:
                self.cards.append(Card(color, action))
                self.cards.append(Card(color, action))
        for _ in range(4):
            self.cards.append(Card(None, "Wild"))
            self.cards.append(Card(None, "Wild Draw Four"))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            return None
        return self.cards.pop()

    def draw_multiple(self, count):
        return [self.draw() for _ in range(count) if self.cards]
