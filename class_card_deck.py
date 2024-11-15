import itertools
import random
from constants import CARD_RANKS, CARD_SUITS


class CardDeck:
    def __init__(self):
        self.deck = list(itertools.product(CARD_RANKS, CARD_SUITS))

    def pull_out_random_card(self):
        if self.deck:
            random_card = random.choice(self.deck)
            random_card_index = self.deck.index(random_card)
            self.deck.pop(random_card_index)

            return random_card
        else:
            return None
