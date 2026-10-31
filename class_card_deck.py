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

    def draw_three_cards(self):
        card1 = self.pull_out_random_card()
        card2 = self.pull_out_random_card()
        card3 = self.pull_out_random_card()
        return card1, card2, card3

    def put_cards_in_deck(self, cards):
        for card in cards:
            self.deck.append(card)
