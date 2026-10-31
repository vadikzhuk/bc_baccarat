import math
import random
from class_item import ITEM_CLASSES, STARTING_GOLD, loadout_problem
from constants import CARD_RANK_VALUES
from game_backend import BARE_FIGHTER, resolve_clash

CARD_WORTH = 0.15        # HP-equivalent value of keeping one rank point in hand
EXTRA_CARD_WORTH = 1.5   # HP-equivalent value of a whole card (brace, slow, disarm)
BRACE_CHANCE = 0.25      # how often the AI expects a defender to brace
RANDOMNESS = 1.5         # softmax temperature: higher = less predictable

# When the AI fires its active skill (if it's usable). Classes not listed use it whenever they can.
ACTIVE_RULES = {
    'Barbarian': lambda player: player.character.rage >= 3,
    'Warlock': lambda player: player.hp > 30,
}

# When the AI uses a consumable it holds (if the timing fits). Items not listed are used as soon as possible.
ITEM_RULES = {
    'Healing Potion': lambda player: player.max_hp() - player.hp >= 12,
    'Smoke Bomb': lambda player: sum(CARD_RANK_VALUES[card[0]] for card in player.hand) < 6 * len(player.hand),
}


def clash_swing(attack_card, defence_card, attacker=BARE_FIGHTER, defender=BARE_FIGHTER):
    """Net HP swing in the attacker's favour, counting heals and card advantage."""
    result = resolve_clash(attack_card, defence_card, attacker, defender)
    swing = (result['damage'] - result['counter_damage']
             + result['attacker_heal'] - result['defender_heal'])
    slows = attack_card[1] == 'C' and not defender.ignores_slow()
    if result['damage'] > 0 and (slows or attack_card[1] == 'S'):
        swing += EXTRA_CARD_WORTH
    if defence_card is None:
        swing -= EXTRA_CARD_WORTH
    return swing


def pick_weighted(options, scores):
    best = max(scores)
    weights = [math.exp((score - best) / RANDOMNESS) for score in scores]
    return random.choices(options, weights)[0]


def wants_active(player):
    rule = ACTIVE_RULES.get(player.character.name)
    return rule(player) if rule else True


def choose_item(usable_items, player):
    """The first usable consumable worth using now, or None."""
    for item in usable_items:
        rule = ITEM_RULES.get(item.name)
        if rule is None or rule(player):
            return item
    return None


def is_useless(item, character):
    """Gear that adds nothing for this class, like a Rapier for a Monk (parry windows don't stack)."""
    return item.parry_window > 0 and character.parry_window >= item.parry_window


def choose_loadout(gold=STARTING_GOLD, character_class=None):
    """Buy items in random order while they fit the budget and slots."""
    loadout = []
    for item in random.sample(ITEM_CLASSES, len(ITEM_CLASSES)):
        if character_class and is_useless(item, character_class):
            continue
        if loadout_problem(loadout + [item], gold) is None:
            loadout.append(item)
    return loadout


def choose_reward(options, player):
    """Rest when badly hurt, otherwise prefer lasting upgrades. options are (kind, label, apply) tuples."""
    preference = ['find', 'train', 'master', 'loot', 'rest']
    if player.hp < 0.6 * player.max_hp():
        preference.insert(0, 'rest')
    return min(options, key=lambda option: preference.index(option[0]))


def shop_in_run(run):
    """Buy in random order whatever fits: empty slots, consumables, and pricier gear as an upgrade."""
    for item in random.sample(run.shop_stock, len(run.shop_stock)):
        replaced = run.replaced_by(item)
        if (replaced and replaced.price >= item.price) or is_useless(item, run.hero.character):
            continue
        if run.buy_problem(item) is None:
            run.buy(item)


def choose_attack(hand, possible_defences, me=BARE_FIGHTER, opponent=BARE_FIGHTER):
    """The defender's card is unknown, so score each attack against every card they might hold."""
    brace_chance = BRACE_CHANCE if opponent.can_brace() else 0
    scores = []
    for card in hand:
        vs_brace = clash_swing(card, None, me, opponent)
        vs_block = vs_brace
        if possible_defences:
            vs_block = sum(clash_swing(card, defence, me, opponent) for defence in possible_defences) / len(possible_defences)
        expected = (1 - brace_chance) * vs_block + brace_chance * vs_brace
        scores.append(expected - CARD_WORTH * CARD_RANK_VALUES[card[0]])
    return pick_weighted(hand, scores)


def choose_defence(hand, possible_attacks, me=BARE_FIGHTER, opponent=BARE_FIGHTER):
    """Returns a card from hand, or None to brace. Attackers tend to lead high, so high cards are weighted up."""
    weights = [CARD_RANK_VALUES[card[0]] for card in possible_attacks]
    total_weight = sum(weights)
    options = hand + [None] if me.can_brace() else list(hand)
    scores = []
    for defence in options:
        swing = sum(w * clash_swing(attack, defence, opponent, me)
                    for attack, w in zip(possible_attacks, weights)) / total_weight
        cost = CARD_WORTH * CARD_RANK_VALUES[defence[0]] if defence else 0
        scores.append(-swing - cost)
    return pick_weighted(options, scores)


def choose_attack_random(hand, possible_defences, me=BARE_FIGHTER, opponent=BARE_FIGHTER):
    return random.choice(hand)


def choose_defence_random(hand, possible_attacks, me=BARE_FIGHTER, opponent=BARE_FIGHTER):
    return random.choice(hand + [None] if me.can_brace() else hand)
