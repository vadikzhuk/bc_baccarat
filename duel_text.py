"""Text shared by the console and pygame front-ends: rules, card names and what happened, as lines."""
from ai_opponent import choose_item, wants_active
from constants import CARD_RANK_VALUES, CARD_SUITS, SUIT_SYMBOLS, ZONES

ZONE_HINTS = {
    'H': 'unblocked hit crits',
    'D': 'a block can only halve it',
    'C': 'on hit: they draw 1 fewer',
    'S': 'on hit: they lose a random card',
}

RULES = """
CARD DUEL - you hold 5 cards. Each turn one player attacks, the other defends.
Both may use their class skill and one item first (announced openly), then both pick a card face-down and reveal.
  Attack: rank = damage (2..10, J=11, Q=12, K=13, A=14), suit = zone hit.
  Same suit as the attack -> BLOCK: damage reduced by your card's rank.
  Same rank as the attack -> PARRY: no damage, attacker takes half back.
  Brace (0) -> play nothing, take the hit, keep the card and draw +1 next refill.
  Zones: """ + ' | '.join(f"{SUIT_SYMBOLS[s]} {ZONES[s]}: {ZONE_HINTS[s]}" for s in CARD_SUITS) + """
Played cards go face-up to the discard pile, so you can count what's left.
Fall to the first attack of a round and you still get a last strike back.
"""


def card_name(card):
    rank, suit = card
    return f"{rank}{SUIT_SYMBOLS[suit]}"


def sorted_hand(hand):
    return sorted(hand, key=lambda card: (CARD_SUITS.index(card[1]), -CARD_RANK_VALUES[card[0]]))


def discard_lines(discard_pile):
    lines = []
    for suit in CARD_SUITS:
        ranks = sorted((card[0] for card in discard_pile if card[1] == suit), key=CARD_RANK_VALUES.get, reverse=True)
        lines.append(f"{SUIT_SYMBOLS[suit]} {ZONES[suit]:<5} {' '.join(ranks) or '-'}")
    return lines


def item_lines(player, item, info, human_used):
    lines = [f">> {player.name} uses {item.name}!"]
    if 'healed' in info:
        lines.append(f"   {player.name} heals {info['healed']} HP.")
    elif 'damage' in info:
        lines.append(f"   {'You hit them' if human_used else 'It hits you'} for {info['damage']} damage.")
    elif 'redrawn' in info:
        lines.append(f"   {player.name} redraws {info['redrawn']} cards.")
    else:
        lines.append(f"   {item.description}")
    return lines


def active_lines(player, info, human_used):
    lines = [f">> {player.name} uses {player.character.active_name}!"]
    if 'stolen' in info and info['stolen']:
        lines.append(f"   {'You steal' if human_used else 'They steal your'} {card_name(info['stolen'])}.")
    elif 'revealed' in info:
        if human_used:
            lines.append(f"   Their hand: {' '.join(card_name(card) for card in sorted_hand(info['revealed']))}")
        else:
            lines.append("   They can see your whole hand this turn.")
    elif 'drawn' in info:
        lines.append(f"   {player.name} pays {player.character.blood_price} HP and draws {info['drawn']} cards.")
    else:
        lines.append(f"   {player.character.active_text}")
    return lines


def ai_prepare(game, ai, attacking):
    """The AI uses its skill and an item if it wants to. Returns what it did, as lines."""
    lines = []
    if wants_active(ai):
        info = game.use_active(ai, attacking)
        if info is not None:
            lines += active_lines(ai, info, human_used=False)
    item = choose_item(game.usable_items(ai, attacking), ai)
    if item:
        lines += item_lines(ai, item, game.use_item(ai, item, attacking), human_used=False)
    return lines


def clash_lines(result, attacker, defender):
    attack_card, defence_card = result['attack_card'], result['defence_card']
    defence = card_name(defence_card) if defence_card else "nothing (brace)"
    lines = [f"{attacker.name} strikes {card_name(attack_card)} at the {ZONES[attack_card[1]]}"
             f"  vs  {defender.name} defends with {defence}"]

    outcome = result['outcome']
    if outcome == 'parry':
        lines.append(f"  PARRY! {defender.name} turns the blow and hits back for {result['counter_damage']}.")
    elif outcome == 'block':
        lines.append(f"  BLOCKED - {result['damage']} damage gets through.")
    elif outcome == 'crit':
        lines.append(f"  CRITICAL hit to the head - {result['damage']} damage!")
    else:
        lines.append(f"  HIT - {result['damage']} damage.")

    if result['attacker_heal']:
        lines.append(f"  {attacker.name} heals {result['attacker_heal']}.")
    if result['defender_heal']:
        lines.append(f"  {defender.name} heals {result['defender_heal']}.")
    if result['effect'] == 'slowed':
        lines.append(f"  {defender.name}'s legs are hit: draws 1 fewer card.")
    elif result['effect'] == 'disarmed':
        lines.append(f"  {defender.name}'s arm is hit: loses {card_name(result['lost_card'])} from hand.")
    return lines
