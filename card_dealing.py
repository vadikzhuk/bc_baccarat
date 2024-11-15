from class_card_deck import CardDeck
from class_player import Player
from time import sleep
from constants import DELAY


def perform_attack(attacker, defender, attacker_card, defender_card):
    damage = defender.calculate_damage(attacker_card, defender_card)
    defender.remove_hp(damage)
    print(f"Damage = {damage}! {defender.name} has {defender.hp}HP left")
    return defender.hp <= 0

def game_loop(player_A, player_B, deck):
    turn_counter = 1
    while len(deck.deck) >= 2:
        # Resolve initiative and decide who is attacking
        player_A.initiative = turn_counter % 2  # 0 or 1 based on counter
        player_B.initiative = (turn_counter + 1) % 2  # Opposite of player_A
        if player_A.initiative > player_B.initiative:
            attacker, defender = player_A, player_B
        else:
            attacker, defender = player_B, player_A
        print(f"{attacker.name} attacks!")
        sleep(DELAY)

        attacker_card = deck.pull_out_random_card()
        print(f"{attacker.name} draws {attacker_card}")
        sleep(DELAY)

        defender_card = deck.pull_out_random_card()
        print(f"{defender.name} draws {defender_card}")
        sleep(DELAY)

        game_over = perform_attack(attacker, defender, attacker_card, defender_card)

        if game_over:
            print(f"{attacker.name} wins at turn {turn_counter}!")
            break

        turn_counter += 1

        sleep(DELAY+5)

    if len(deck.deck) < 2:
        print("Game ended in a draw - ran out of cards!")


if __name__ == "__main__":
    deck = CardDeck()
    player_A = Player("Gandalf")
    player_B = Player("Balrog")

    game_loop(player_A, player_B, deck)
