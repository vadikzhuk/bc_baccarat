from class_card_deck import CardDeck
from class_player import Player


class Game:
    def __init__(self, player_A_name, player_B_name, class_A="Warrior", class_B="Warrior"):
        self.deck = CardDeck()
        self.player_A = Player(player_A_name, character_class=class_A)
        self.player_B = Player(player_B_name, character_class=class_B)

        # Cyberpunk balance adjustments
        if class_A == "Cyborg Tank":
            self.player_A.hp += 10
        if class_B == "Cyborg Tank":
            self.player_B.hp += 10

        if class_A == "Corporate Agent":
            self.player_A.hp -= 5
            self.player_A.initiative += 1
        if class_B == "Corporate Agent":
            self.player_B.hp -= 5
            self.player_B.initiative += 1

        self.turn_counter = 1
        self.game_over = False
        self.winner = None

        # Flags for Netrunner hacking
        self.disable_next_ability = {self.player_A.name: False, self.player_B.name: False}

    def get_current_turn(self):
        """Resolve initiative based on turn counter."""
        self.player_A.initiative = self.turn_counter % 2
        self.player_B.initiative = (self.turn_counter + 1) % 2

        if self.player_A.initiative > self.player_B.initiative:
            return self.player_A, self.player_B
        else:
            return self.player_B, self.player_A

    def draw_cards(self, attacker):
        """Handles normal draw and Black-Market Dealer's extra draw."""
        if attacker.character_class == "Black-Market Dealer" and not attacker.used_once_per_game:
            attacker.used_once_per_game = True
            card1 = self.deck.pull_out_random_card()
            card2 = self.deck.pull_out_random_card()
            # Pick the higher damage rank
            chosen = card1 if card1[0] >= card2[0] else card2
            defender_card = self.deck.pull_out_random_card()
            return chosen, defender_card
        else:
            return self.deck.pull_out_random_card(), self.deck.pull_out_random_card()

    def perform_attack(self, attacker, defender, attacker_card, defender_card):
        # Check for non-attack special actions
        special = attacker.heal_or_special_action()
        if special == True:
            return 0  # heal or passive effect, no damage dealt
        elif special == "disable_opponent":
            self.disable_next_ability[defender.name] = True
            return 0

        # Step 1: Calculate base damage
        damage = defender.calculate_damage(attacker_card, defender_card)

        # Step 2: Attacker bonus (skip if hacked by Netrunner)
        if not self.disable_next_ability[attacker.name]:
            damage = attacker.attack_bonus(damage)

        # Step 3: Defender’s special defenses (skip if hacked)
        if not self.disable_next_ability[defender.name]:
            damage = defender.apply_defense_abilities(damage, attacker_card, defender_card)

        # Reset disable flag after use
        self.disable_next_ability[attacker.name] = False
        self.disable_next_ability[defender.name] = False

        # Step 4: Apply damage
        defender.remove_hp(damage)

        # Step 5: Post-attack effects (Techno-Shaman feedback)
        if not self.disable_next_ability[attacker.name]:
            extra = attacker.on_attack(damage)
            if extra > 0:
                defender.remove_hp(extra)
                damage += extra

        # Step 6: Victory check
        if defender.hp <= 0:
            self.game_over = True
            self.winner = attacker.name

        return damage

    def advance_turn(self):
        self.turn_counter += 1
        # End-of-turn passives
        self.player_A.end_of_turn()
        self.player_B.end_of_turn()

        if len(self.deck.deck) < 4:
            self.game_over = True  # Draw if deck is exhausted

    def is_game_over(self):
        return self.game_over

    def get_winner(self):
        return self.winner
