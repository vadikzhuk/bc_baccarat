import random
from class_character import Character
from constants import CARD_RANK_VALUES


class Player():
    def __init__(self, player_name, character=None, items=()):
        self.name = player_name
        self.character = character or Character()
        self.sex = random.choice(('male', 'female'))  # only picks the portrait
        self.equipment = [item for item in items if item.slot != 'consumable']
        self.consumables = [item for item in items if item.slot == 'consumable']
        self.max_hp_bonus = 0  # permanent, from run rewards and enemy scaling
        self.hp = self.max_hp()
        self.initiative = 1
        self.prepare_for_duel()

    def prepare_for_duel(self):
        """Clear everything that only lasts one duel. HP, items and max HP carry over between duels in a run."""
        self.hand = []
        # One-off change to the next refill: -1 when slowed, +1 after bracing
        self.hand_size_modifier = 0
        self.armed_items = []  # consumables in effect for the current clash
        self.used_item_this_turn = False
        self.character.reset()

    def remove_hp(self, amount_to_remove):
        # HP can go negative: overkill breaks ties when both players fall in the same round
        self.hp -= amount_to_remove

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp())

    def max_hp(self):
        return self.character.max_hp + self.max_hp_bonus + sum(item.hp_bonus for item in self.equipment)

    def hand_limit(self):
        return (self.character.hand_size + self.hand_size_modifier
                + sum(item.hand_size_bonus for item in self.equipment))

    def play_card(self, card):
        self.hand.remove(card)
        return card

    def discard_random_card(self):
        if not self.hand:
            return None
        card = random.choice(self.hand)
        self.hand.remove(card)
        return card

    def end_clash(self):
        self.character.on_clash_end()
        self.armed_items = []

    # Rule hooks used by resolve_clash, combined over the class and everything equipped or armed
    def modifiers(self):
        return [self.character, *self.equipment, *self.armed_items]

    def attack_bonus(self):
        return sum(modifier.attack_bonus() for modifier in self.modifiers())

    def unblocked_bonus(self):
        return sum(modifier.unblocked_bonus for modifier in self.modifiers())

    def crit_multiplier(self):
        return self.character.crit_multiplier

    def crit_immune(self):
        return any(modifier.crit_immune for modifier in self.modifiers())

    def parry_window(self):
        return max(modifier.parry_window for modifier in self.modifiers())

    def can_brace(self):
        return all(modifier.can_brace for modifier in self.modifiers())

    def blocks_any_suit(self):
        return any(modifier.blocks_any_suit() for modifier in self.modifiers())

    def is_unblockable(self):
        return any(modifier.is_unblockable() for modifier in self.modifiers())

    def block_halves_at_most(self):
        return any(modifier.block_halves_at_most for modifier in self.modifiers())

    def damage_reduction(self):
        return sum(modifier.damage_reduction for modifier in self.modifiers())

    def brace_reduction(self):
        return sum(modifier.brace_reduction for modifier in self.modifiers())

    def ignores_slow(self):
        return any(modifier.ignores_slow for modifier in self.modifiers())

    def defence_heal(self, defence_card):
        return sum(modifier.defence_heal(defence_card) for modifier in self.modifiers())

    def attack_heal(self, attack_card, damage):
        return sum(modifier.attack_heal(attack_card, damage) for modifier in self.modifiers())

    def sees_opponent_hand(self):
        return any(modifier.sees_opponent_hand() for modifier in self.modifiers())

    def calculate_damage(self, attack_card, defence_card):
        attack_rank, attack_zone = attack_card
        defence_rank, defence_zone = defence_card
        damage = CARD_RANK_VALUES[attack_rank]
        if defence_zone == attack_zone:
            damage = max(damage - CARD_RANK_VALUES[defence_rank], 0)

        return damage
