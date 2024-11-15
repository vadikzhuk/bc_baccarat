from constants import CARD_RANK_VALUES


class Player():
    def __init__(self, player_name):
        self.name = player_name
        self.hp = 50
        self.initiative = 1

    def remove_hp(self, amount_to_remove):
        self.hp = max(self.hp - amount_to_remove, 0)

    def calculate_damage(self, attack_card, defence_card):
        attack_rank, attack_zone = attack_card
        defence_rank, defence_zone = defence_card
        damage = CARD_RANK_VALUES[attack_rank]
        if defence_zone == attack_zone:
            damage = max(damage - CARD_RANK_VALUES[defence_rank], 0)

        return damage
