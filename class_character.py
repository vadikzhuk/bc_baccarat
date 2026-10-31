from constants import CARD_RANK_VALUES, HAND_SIZE, HEAD_CRIT_MULTIPLIER, STARTING_HP


def timing_allows(timing, attacking):
    """Timing is 'attack' or 'defend' (only usable on that side of the clash) or 'any'."""
    return timing == 'any' or timing == ('attack' if attacking else 'defend')


class Modifier():
    """Neutral rule hooks. Classes and items override the ones they bend; Player combines them.
    Fixed values are attributes, values that depend on state are methods.
    """
    unblocked_bonus = 0
    parry_window = 0
    can_brace = True
    crit_immune = False             # crits against you deal normal damage
    block_halves_at_most = False    # every suit's block works like a Body block against you attacking
    damage_reduction = 0            # taken off every clash hit against you
    brace_reduction = 0             # taken off the hit when you brace
    ignores_slow = False
    hand_size_bonus = 0
    hp_bonus = 0

    def attack_bonus(self):
        return 0

    def blocks_any_suit(self):
        return False

    def is_unblockable(self):
        return False

    def defence_heal(self, defence_card):
        return 0

    def attack_heal(self, attack_card, damage):
        return 0

    def sees_opponent_hand(self):
        return False


class Character(Modifier):
    """Classless fighter. Subclasses bend one rule (passive) and add one active skill.
    Armed actives last for the current clash; on_clash_end() disarms them.
    """
    name = "Fighter"
    max_hp = STARTING_HP
    hand_size = HAND_SIZE
    passive_text = "No special rules."
    crit_multiplier = HEAD_CRIT_MULTIPLIER

    active_name = None
    active_text = ""
    active_timing = 'any'
    active_cooldown = 0

    def __init__(self):
        self.reset()

    def reset(self):
        """Clear per-duel state (cooldowns, armed skills) so a character can fight again in a run."""
        self.cooldown_left = 0
        self.armed = False

    # Lifecycle hooks used by Game
    def on_damage_taken(self, damage):
        pass

    def on_clash_end(self):
        self.armed = False

    def tick_cooldown(self):
        self.cooldown_left = max(self.cooldown_left - 1, 0)

    def can_use_active(self, player, attacking):
        if self.active_name is None or self.cooldown_left > 0:
            return False
        return timing_allows(self.active_timing, attacking)

    def use_active(self, game, player, opponent):
        """Arms the skill by default. Returns a dict of what happened, for display."""
        self.cooldown_left = self.active_cooldown
        self.armed = True
        return {}

    def status_text(self):
        if self.active_name is None:
            return ""
        return f"{self.active_name} {'ready' if self.cooldown_left == 0 else f'in {self.cooldown_left}'}"


class Barbarian(Character):
    name = "Barbarian"
    max_hp = 54
    passive_text = "Rage: +1 rage (max 5) each time you take damage. Can't brace."
    active_name = "Unleash"
    active_text = "Spend all rage: +2 damage per rage on this attack."
    active_timing = 'attack'
    max_rage = 5
    can_brace = False

    def reset(self):
        super().reset()
        self.rage = 0

    def attack_bonus(self):
        return 2 * self.rage if self.armed else 0

    def on_damage_taken(self, damage):
        if damage > 0:
            self.rage = min(self.rage + 1, self.max_rage)

    def on_clash_end(self):
        if self.armed:
            self.rage = 0
        super().on_clash_end()

    def can_use_active(self, player, attacking):
        return self.rage > 0 and super().can_use_active(player, attacking)

    def status_text(self):
        return f"rage {self.rage}/{self.max_rage}"


class Rogue(Character):
    name = "Rogue"
    max_hp = 52
    unblocked_bonus = 4
    passive_text = "Backstab: unblocked hits deal +4 damage."
    active_name = "Pickpocket"
    active_text = "Steal a random card from the opponent's hand."
    active_cooldown = 3

    def use_active(self, game, player, opponent):
        super().use_active(game, player, opponent)
        stolen = opponent.discard_random_card()
        if stolen:
            player.hand.append(stolen)
        return {'stolen': stolen}


class Assassin(Character):
    name = "Assassin"
    max_hp = 50
    crit_multiplier = 2
    passive_text = "Unblocked Head (♥) hits deal x2 instead of x1.5."
    active_name = "Mark"
    active_text = "See the opponent's whole hand this turn."
    active_cooldown = 2

    def sees_opponent_hand(self):
        return self.armed

    def use_active(self, game, player, opponent):
        super().use_active(game, player, opponent)
        return {'revealed': list(opponent.hand)}


class Paladin(Character):
    name = "Paladin"
    max_hp = 45
    passive_text = "Defending with a ♥ card heals you for a third of its rank."
    active_name = "Divine Shield"
    active_text = "This turn your defence card blocks any suit."
    active_timing = 'defend'
    active_cooldown = 6

    def blocks_any_suit(self):
        return self.armed

    def defence_heal(self, defence_card):
        return CARD_RANK_VALUES[defence_card[0]] // 3 if defence_card[1] == 'H' else 0


class Monk(Character):
    name = "Monk"
    max_hp = 42
    parry_window = 1
    passive_text = "Parry when ranks are within 1 of each other (a 7 parries 6, 7 or 8)."
    active_name = "Iron Palm"
    active_text = "This attack can't be blocked, only parried."
    active_timing = 'attack'
    active_cooldown = 4

    def is_unblockable(self):
        return self.armed


class Warlock(Character):
    name = "Warlock"
    max_hp = 58
    passive_text = "Life drain: every hit heals you for a third of the damage dealt."
    active_name = "Blood Pact"
    active_text = "Pay 3 HP, draw 2 cards."
    active_cooldown = 2
    blood_price = 3

    def attack_heal(self, attack_card, damage):
        return damage // 3

    def can_use_active(self, player, attacking):
        return player.hp > self.blood_price and super().can_use_active(player, attacking)

    def use_active(self, game, player, opponent):
        super().use_active(game, player, opponent)
        player.remove_hp(self.blood_price)
        for _ in range(2):
            card = game.draw_card()
            if card:
                player.hand.append(card)
        return {'drawn': 2}


CHARACTER_CLASSES = [Barbarian, Rogue, Assassin, Paladin, Monk, Warlock]
