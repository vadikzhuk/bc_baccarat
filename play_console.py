import random
from ai_opponent import choose_attack, choose_defence, choose_loadout
from class_character import CHARACTER_CLASSES
from class_item import ITEM_CLASSES, MAX_CONSUMABLES, STARTING_GOLD, loadout_problem
from class_player import Player
from constants import ZONES
from duel_text import (RULES, ZONE_HINTS, active_lines, ai_prepare, card_name, clash_lines, discard_lines,
                       item_lines, sorted_hand)
from game_backend import Game

def describe_class(cls):
    return (f"{cls.name} - {cls.max_hp} HP\n"
            f"      Passive: {cls.passive_text}\n"
            f"      {cls.active_name} ({cls.active_timing}): {cls.active_text}")


def ask_class():
    print("Choose your class:")
    for number, cls in enumerate(CHARACTER_CLASSES, start=1):
        print(f"   {number}) {describe_class(cls)}")
    while True:
        answer = input(f"Choose [1-{len(CHARACTER_CLASSES)}]: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(CHARACTER_CLASSES):
            return CHARACTER_CLASSES[int(answer) - 1]
        print("  Not a valid choice.")


def ask_loadout():
    print(f"\nShop - {STARTING_GOLD} gold. One weapon, one armor, up to {MAX_CONSUMABLES} consumables (each used once).")
    for number, item in enumerate(ITEM_CLASSES, start=1):
        print(f"   {number:>2}) {item.name:<15} {item.slot:<10} {item.price}g  {item.description}")
    loadout = []
    while True:
        gold_left = STARTING_GOLD - sum(item.price for item in loadout)
        bought = ', '.join(item.name for item in loadout) or 'nothing'
        answer = input(f"Bought: {bought} | {gold_left}g left. Item number to buy, -number to sell, Enter when done: ").strip()
        if not answer:
            return loadout
        selling = answer.startswith('-')
        number = answer.lstrip('-')
        if not number.isdigit() or not 1 <= int(number) <= len(ITEM_CLASSES):
            print("  Not a valid choice.")
            continue
        item = ITEM_CLASSES[int(number) - 1]
        if selling:
            if item in loadout:
                loadout.remove(item)
            continue
        problem = loadout_problem(loadout + [item])
        if problem:
            print(f"  Can't buy {item.name}: {problem}.")
        else:
            loadout.append(item)


def player_line(player):
    character = player.character
    return f"{player.name} the {character.name}: {player.hp}/{player.max_hp()} HP, {character.status_text()}"


def gear_line(player):
    equipment = ', '.join(item.name for item in player.equipment) or 'none'
    consumables = ', '.join(item.name for item in player.consumables) or 'none'
    return f"      gear: {equipment} | items: {consumables}"


def show_table(game, human, ai, attacker):
    role = "you ATTACK" if attacker is human else "you DEFEND"
    if game.is_last_strike():
        role += " (LAST STRIKE)"
    print(f"\n========== Turn {game.turn_counter}: {role} ==========")
    print(player_line(human))
    print(gear_line(human))
    print(f"{player_line(ai)}, {len(ai.hand)} cards in hand   |   deck: {len(game.deck.deck)}")
    print(gear_line(ai))
    print("Discard pile:")
    for line in discard_lines(game.discard_pile):
        print(f"   {line}")


def ask_active(game, human, attacking):
    character = human.character
    if not character.can_use_active(human, attacking):
        return
    answer = input(f"Use {character.active_name}? ({character.active_text}) [y/N]: ").strip().lower()
    if answer == 'y':
        print_lines(active_lines(human, game.use_active(human, attacking), human_used=True))


def ask_item(game, human, attacking):
    items = game.usable_items(human, attacking)
    if not items:
        return
    options = ' '.join(f"{number}) {item.name}" for number, item in enumerate(items, start=1))
    answer = input(f"Use an item? {options} [Enter = no]: ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(items):
        item = items[int(answer) - 1]
        print_lines(item_lines(human, item, game.use_item(human, item, attacking), human_used=True))


def print_lines(lines):
    for line in lines:
        print(line)


def ask_card(hand, can_brace):
    hand = sorted_hand(hand)
    print("Your hand:")
    for number, card in enumerate(hand, start=1):
        print(f"   {number}) {card_name(card):<4} {ZONES[card[1]]:<5} ({ZONE_HINTS[card[1]]})")
    if can_brace:
        print("   0) Brace - keep your card, take the hit")

    lowest = 0 if can_brace else 1
    while True:
        answer = input(f"Choose [{lowest}-{len(hand)}]: ").strip()
        if answer.isdigit() and lowest <= int(answer) <= len(hand):
            return hand[int(answer) - 1] if int(answer) else None
        print("  Not a valid choice.")


def main():
    print(RULES)
    human_class = ask_class()
    human_items = ask_loadout()
    ai_class = random.choice(CHARACTER_CLASSES)
    ai_items = choose_loadout(character_class=ai_class)
    game = Game(Player("Hero", human_class(), [item() for item in human_items]),
                Player("Rival", ai_class(), [item() for item in ai_items]))
    print(f"\nYour rival is a {describe_class(ai_class)}")
    print(f"      Bought: {', '.join(item.name for item in ai_items) or 'nothing'}")
    play_duel(game)


def play_duel(game):
    """Human is player_A, the AI is player_B. Returns True if the human won."""
    human, ai = game.player_A, game.player_B
    while not game.is_game_over():
        attacker, defender = game.get_current_turn()
        show_table(game, human, ai, attacker)

        # Skills are announced openly: attacker first, then the defender reacts
        if attacker is human:
            ask_active(game, human, attacking=True)
            ask_item(game, human, attacking=True)
            print_lines(ai_prepare(game, ai, attacking=False))
        else:
            print_lines(ai_prepare(game, ai, attacking=True))
            ask_active(game, human, attacking=False)
            ask_item(game, human, attacking=False)

        # The AI only ever sees its own hand and the discard pile (or your hand if it used Mark), never your pick
        if attacker is human:
            attack_card = ask_card(human.hand, can_brace=False)
            defence_card = choose_defence(ai.hand, game.possible_opponent_cards(ai), ai, human)
        else:
            attack_card = choose_attack(ai.hand, game.possible_opponent_cards(ai), ai, human)
            print(f"{ai.name} has chosen an attack card...")
            defence_card = ask_card(human.hand, can_brace=human.can_brace())

        result = game.play_clash(attacker, defender, attack_card, defence_card)
        print()
        print_lines(clash_lines(result, attacker, defender))
        game.advance_turn()
        if not game.is_game_over():
            input("\n[Enter] next turn")

    print(f"\nFinal: {human.name} {human.hp} HP, {ai.name} {ai.hp} HP")
    print(f"{game.get_winner()} wins!" if game.get_winner() else "Both fall - it's a draw!")
    return game.get_winner() == human.name


if __name__ == "__main__":
    main()
