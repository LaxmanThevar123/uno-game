class Card:
    COLORS = ["Red", "Yellow", "Green", "Blue"]
    TYPES = list(range(10)) + list(range(1, 10)) + ["Skip", "Reverse", "Draw Two"] * 2
    WILDS = ["Wild", "Wild Draw Four"]

    def __init__(self, color, card_type):
        self.color = color
        self.card_type = card_type

    def is_wild(self):
        return self.color is None

    def matches(self, other):
        if self.is_wild():
            return True
        return self.color == other.color or self.card_type == other.card_type

    def __str__(self):
        if self.is_wild():
            return f"[{self.card_type}]"
        return f"[{self.color} {self.card_type}]"
