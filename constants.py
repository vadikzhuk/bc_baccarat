# Card deck
CARD_SUITS = ['H', 'D', 'C', 'S']
CARD_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
CARD_RANK_VALUES = {
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    '10': 10,
    'J': 11,
    'Q': 12,
    'K': 13,
    'A': 14
}

# Suit = body zone the card attacks or guards
ZONES = {'H': 'Head', 'D': 'Body', 'C': 'Legs', 'S': 'Arms'}
SUIT_SYMBOLS = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}

# Duel rules
STARTING_HP = 50
HAND_SIZE = 5
HEAD_CRIT_MULTIPLIER = 1.5

DELAY = 3 # in seconds

# Pygame settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 800
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
FPS = 60
