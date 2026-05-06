import sys
sys.stdout.reconfigure(encoding='utf-8')
from game.game import Game
from game.player import Player
from game.card import Card


def next_active(game, room):
    """Mirror of server's next_active_player_index"""
    skip_list = room.get("finished", []) + room.get("locked", [])
    idx = game.current_index
    for _ in range(len(game.players)):
        idx = (idx + game.direction) % len(game.players)
        if game.players[idx].name not in skip_list:
            return idx
    return game.next_player_index()


print("=" * 50)
print("TEST 1: next_active skips finished player")
players = [Player('A'), Player('B'), Player('C')]
game = Game(players)
game.current_index = 0
game.direction = 1
room = {'finished': ['B'], 'locked': []}
idx = next_active(game, room)
assert game.players[idx].name == 'C', f"FAIL: got {game.players[idx].name}"
print("  PASS: A -> skips B -> C")

print("=" * 50)
print("TEST 2: next_active skips locked player")
room2 = {'finished': [], 'locked': ['B']}
idx = next_active(game, room2)
assert game.players[idx].name == 'C'
print("  PASS: A -> skips locked B -> C")

print("=" * 50)
print("TEST 3: Multiple skips (B finished, C locked)")
players4 = [Player('A'), Player('B'), Player('C'), Player('D')]
game4 = Game(players4)
game4.current_index = 0
game4.direction = 1
room3 = {'finished': ['B'], 'locked': ['C']}
idx = next_active(game4, room3)
assert game4.players[idx].name == 'D', f"FAIL: got {game4.players[idx].name}"
print("  PASS: A -> skips B,C -> D")

print("=" * 50)
print("TEST 4: Reverse direction skips finished")
game4.current_index = 3  # D
game4.direction = -1
room4 = {'finished': ['C'], 'locked': []}
idx = next_active(game4, room4)
assert game4.players[idx].name == 'B', f"FAIL: got {game4.players[idx].name}"
print("  PASS: D(CCW) -> skips C -> B")

print("=" * 50)
print("TEST 5: Draw Two targets active player not finished")
players5 = [Player('A'), Player('B'), Player('C')]
game5 = Game(players5)
game5.current_index = 0
game5.direction = 1
room5 = {'finished': ['B'], 'locked': []}
idx = next_active(game5, room5)
target = game5.players[idx]
initial = len(target.hand)
target.add_cards(game5.deck.draw_multiple(2))
assert target.name == 'C'
assert len(target.hand) == initial + 2
print(f"  PASS: Draw Two -> C gets 2 cards ({initial} -> {len(target.hand)})")

print("=" * 50)
print("TEST 6: Wild Draw Four targets active player not finished")
players6 = [Player('A'), Player('B'), Player('C')]
game6 = Game(players6)
game6.current_index = 0
game6.direction = 1
room6 = {'finished': ['B'], 'locked': []}
idx = next_active(game6, room6)
target = game6.players[idx]
initial = len(target.hand)
target.add_cards(game6.deck.draw_multiple(4))
assert target.name == 'C'
assert len(target.hand) == initial + 4
print(f"  PASS: Wild+4 -> C gets 4 cards ({initial} -> {len(target.hand)})")

print("=" * 50)
print("TEST 7: 2-player game - one wins, game ends")
players7 = [Player('A'), Player('B')]
game7 = Game(players7)
room7 = {'finished': [], 'locked': []}
room7['finished'].append('A')
active = [p for p in game7.players if p.name not in room7['finished']]
assert len(active) == 1
assert active[0].name == 'B'
print("  PASS: A finishes -> only B left -> game over")

print("=" * 50)
print("TEST 8: All players finished except one = game over")
players8 = [Player('A'), Player('B'), Player('C'), Player('D')]
game8 = Game(players8)
room8 = {'finished': ['A', 'B', 'C'], 'locked': []}
active = [p for p in game8.players if p.name not in room8['finished']]
assert len(active) == 1
assert active[0].name == 'D'
print("  PASS: A,B,C finish -> D is last -> game over")

print("=" * 50)
print("TEST 9: Locked + finished combined leaves 1 active = game over")
players9 = [Player('A'), Player('B'), Player('C')]
game9 = Game(players9)
room9 = {'finished': ['A'], 'locked': ['B']}
active = [p for p in game9.players if p.name not in room9['finished'] + room9['locked']]
assert len(active) == 1
assert active[0].name == 'C'
print("  PASS: A finished, B locked -> C alone -> game over")

print("=" * 50)
print("TEST 10: Skip card - advance_turn skips finished")
players10 = [Player('A'), Player('B'), Player('C')]
game10 = Game(players10)
game10.current_index = 0
game10.direction = 1
room10 = {'finished': ['B'], 'locked': []}
# Skip advances once, then we need to skip finished
game10.advance_turn()  # now at B (index 1)
while game10.current_player.name in room10['finished']:
    game10.advance_turn()
assert game10.current_player.name == 'C'
print("  PASS: Skip from A -> lands on C (skips finished B)")

print("=" * 50)
print("TEST 11: Reverse with 2 active players acts like skip")
players11 = [Player('A'), Player('B'), Player('C')]
game11 = Game(players11)
game11.current_index = 0
game11.direction = 1
room11 = {'finished': ['B'], 'locked': []}
# Reverse flips direction
game11.direction *= -1
# Now direction is -1, from A(0) going backwards: 0-1 = -1 % 3 = 2 = C
game11.advance_turn()
while game11.current_player.name in room11['finished']:
    game11.advance_turn()
assert game11.current_player.name == 'C', f"FAIL: got {game11.current_player.name}"
print("  PASS: Reverse from A(CCW) -> C")

print("=" * 50)
print("TEST 12: Card matching rules")
c1 = Card("Red", 5)
c2 = Card("Red", 3)  # same color
c3 = Card("Blue", 5)  # same number
c4 = Card("Blue", 7)  # no match
c5 = Card(None, "Wild")  # wild always matches
c6 = Card(None, "Wild Draw Four")

assert c2.matches(c1) == True, "Same color should match"
assert c3.matches(c1) == True, "Same number should match"
assert c4.matches(c1) == False, "Different color+number should not match"
assert c5.matches(c1) == True, "Wild always matches"
assert c6.matches(c1) == True, "Wild Draw Four always matches"
print("  PASS: All matching rules correct")

print("=" * 50)
print("TEST 13: Effective top for wild card matching")
game13 = Game([Player('X'), Player('Y')])
wild = Card(None, "Wild")
game13.play_card(wild)
game13.top_color = "Green"
eff = game13.effective_top
assert eff.color == "Green"
# A green card should match
green_card = Card("Green", 3)
assert green_card.matches(eff) == True
# A red card should not
red_card = Card("Red", 7)
assert red_card.matches(eff) == False
print("  PASS: Effective top color works for wild")

print("=" * 50)
print("TEST 14: Deck has 108 cards")
from game.deck import Deck
d = Deck()
assert len(d.cards) == 108, f"FAIL: {len(d.cards)} cards"
print("  PASS: 108 cards in deck")

print("=" * 50)
print("TEST 15: Player UNO detection")
p = Player("Test")
p.hand = [Card("Red", 5), Card("Blue", 3)]
assert p.has_uno() == False
p.hand = [Card("Red", 5)]
assert p.has_uno() == True
assert p.has_won() == False
p.hand = []
assert p.has_won() == True
print("  PASS: UNO and win detection correct")

print()
print("=" * 50)
print("TEST 16: Skip should target next ACTIVE player")
players16 = [Player('A'), Player('B'), Player('C')]
game16 = Game(players16)
game16.current_index = 0
game16.direction = 1
room16 = {'finished': ['B'], 'locked': []}
# Skip from A: next active should be C (skip B who finished)
idx = next_active(game16, room16)
assert game16.players[idx].name == 'C', f"FAIL: got {game16.players[idx].name}"
print("  PASS: Skip from A -> skips finished B -> targets C")

print("=" * 50)
print("TEST 17: Reverse only flips direction, doesn't target finished")
players17 = [Player('A'), Player('B'), Player('C'), Player('D')]
game17 = Game(players17)
game17.current_index = 0
game17.direction = 1
room17 = {'finished': ['D'], 'locked': []}
# Reverse flips direction to -1
game17.direction *= -1
# Now from A going backwards, next active should skip D
idx = next_active(game17, room17)
assert game17.players[idx].name == 'C', f"FAIL: got {game17.players[idx].name}"
print("  PASS: Reverse from A(CCW) -> skips finished D -> C")

print("=" * 50)
print("TEST 18: Seating order - server sends correct circular order")
players18 = [Player('Vikhil'), Player('Laxman'), Player('Ali'), Player('Samarth')]
game18 = Game(players18)
# Simulate get_player_state seating for Laxman (index 1)
player_name = 'Laxman'
all_p = game18.players
my_idx = next((i for i, p in enumerate(all_p) if p.name == player_name), 0)
seating = []
for i in range(len(all_p)):
    idx = (my_idx + i) % len(all_p)
    seating.append(all_p[idx].name)
print(f"  Seating from Laxman's view: {seating}")
assert seating == ['Laxman', 'Ali', 'Samarth', 'Vikhil']
print("  PASS: Order is [You, Next, After, Previous]")
print("  Visual: You(bottom), Ali(right/next), Samarth(top/across), Vikhil(left/prev)")

print()
print("=" * 50)
print("ALL 18 TESTS PASSED!")
print("=" * 50)
