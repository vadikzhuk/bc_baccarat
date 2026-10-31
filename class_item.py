from class_character import Modifier, timing_allows

STARTING_GOLD = 10
MAX_CONSUMABLES = 3


class Item(Modifier):
    """Weapons and armor bend rules for the whole duel. Consumables are used once, during the skill phase."""
    name = ""
    slot = ""
    price = 0
    description = ""


# Weapons
class Rapier(Item):
    name = "Rapier"
    slot = 'weapon'
    price = 5
    parry_window = 1
    description = "Parry when ranks are within 1 of each other (no extra effect for a Monk)."


class Greataxe(Item):
    name = "Greataxe"
    slot = 'weapon'
    price = 4
    hand_size_bonus = -1
    description = "+3 damage on every attack, but you hold one card fewer."

    def attack_bonus(self):
        return 3


class WarHammer(Item):
    name = "War Hammer"
    slot = 'weapon'
    price = 2
    block_halves_at_most = True
    description = "Crushing: a block can at most halve your damage, whatever the suit."


# Armor
class Helm(Item):
    name = "Helm"
    slot = 'armor'
    price = 2
    crit_immune = True
    description = "Head (♥) hits against you never crit."


class Chainmail(Item):
    name = "Chainmail"
    slot = 'armor'
    price = 5
    damage_reduction = 2
    description = "Every hit against you deals 2 less damage."


class PaddedVest(Item):
    name = "Padded Vest"
    slot = 'armor'
    price = 3
    hp_bonus = 8
    description = "+8 max HP."


class Boots(Item):
    name = "Boots"
    slot = 'armor'
    price = 3
    brace_reduction = 4
    ignores_slow = True
    description = "Bracing takes 4 off the hit, and Legs (♣) hits never slow you."


class Consumable(Item):
    """Used once per duel during the skill phase, at most one per turn.
    arms=True: works like an armed skill for this clash only. arms=False: takes effect immediately in use().
    """
    slot = 'consumable'
    timing = 'any'
    arms = False

    def can_use(self, attacking):
        return timing_allows(self.timing, attacking)

    def use(self, game, player, opponent):
        """Returns a dict of what happened, for display."""
        return {}


class HealingPotion(Consumable):
    name = "Healing Potion"
    price = 3
    description = "Heal 8 HP."

    def use(self, game, player, opponent):
        hp_before = player.hp
        player.heal(8)
        return {'healed': player.hp - hp_before}


class Whetstone(Consumable):
    name = "Whetstone"
    price = 1
    timing = 'attack'
    arms = True
    description = "+4 damage on this attack."

    def attack_bonus(self):
        return 4


class Buckler(Consumable):
    name = "Buckler"
    price = 1
    timing = 'defend'
    arms = True
    description = "This turn your defence card blocks any suit."

    def blocks_any_suit(self):
        return True


class SmokeBomb(Consumable):
    name = "Smoke Bomb"
    price = 2
    description = "Discard your hand and draw the same number of new cards."

    def use(self, game, player, opponent):
        card_count = len(player.hand)
        game.discard_pile.extend(player.hand)
        player.hand = []
        for _ in range(card_count):
            card = game.draw_card()
            if card:
                player.hand.append(card)
        return {'redrawn': card_count}


class ThrowingKnife(Consumable):
    name = "Throwing Knife"
    price = 2
    description = "Deal 5 damage right now. Can't be blocked."

    def use(self, game, player, opponent):
        opponent.remove_hp(5)
        return {'damage': 5}


ITEM_CLASSES = [Rapier, Greataxe, WarHammer,
                Helm, Chainmail, PaddedVest, Boots,
                HealingPotion, Whetstone, Buckler, SmokeBomb, ThrowingKnife]


def loadout_problem(item_classes, gold=STARTING_GOLD):
    """Returns why a set of items can't be bought together, or None if it's fine."""
    if sum(item.price for item in item_classes) > gold:
        return "not enough gold"
    return slot_problem(item_classes)


def slot_problem(items):
    """Returns why these items can't all be carried at once, or None if they can."""
    slots = [item.slot for item in items]
    for slot in ('weapon', 'armor'):
        if slots.count(slot) > 1:
            return f"only one {slot} can be equipped"
    if slots.count('consumable') > MAX_CONSUMABLES:
        return f"at most {MAX_CONSUMABLES} consumables"
    return None
