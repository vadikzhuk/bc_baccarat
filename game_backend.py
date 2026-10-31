import itertools
import math
from class_card_deck import CardDeck
from class_player import Player
from constants import CARD_RANKS, CARD_SUITS, CARD_RANK_VALUES

BARE_FIGHTER = Player("Bare fighter")  # no class, no items: plain card rules


def resolve_clash(attack_card, defence_card, attacker=BARE_FIGHTER, defender=BARE_FIGHTER):
    """Resolve one attack against one blind defence. defence_card is None when the defender braces.
    attacker/defender are Players; their class, equipment and armed skills/items bend the rules.

    Returns a dict: outcome ('parry', 'block', 'hit' or 'crit'), damage, counter_damage,
    attacker_heal, defender_heal.
    """
    attack_rank, attack_suit = attack_card
    attack_value = CARD_RANK_VALUES[attack_rank] + attacker.attack_bonus()
    result = {'outcome': 'hit', 'damage': 0, 'counter_damage': 0, 'attacker_heal': 0, 'defender_heal': 0}

    if defence_card is not None:
        defence_rank, defence_suit = defence_card
        defence_value = CARD_RANK_VALUES[defence_rank]
        result['defender_heal'] = defender.defence_heal(defence_card)

        if abs(defence_value - CARD_RANK_VALUES[attack_rank]) <= defender.parry_window():
            counter_damage = max(attack_value // 2 - attacker.damage_reduction(), 0)
            result.update(outcome='parry', counter_damage=counter_damage)
            return result

        if (defence_suit == attack_suit or defender.blocks_any_suit()) and not attacker.is_unblockable():
            damage = max(attack_value - defence_value, 0)
            if attack_suit == 'D' or attacker.block_halves_at_most():  # Body: a block can at most halve the damage
                damage = max(damage, math.ceil(attack_value / 2))
            return land_hit(result, 'block', damage, attack_card, attacker, defender)

    damage = attack_value + attacker.unblocked_bonus()
    if defence_card is None:
        damage = max(damage - defender.brace_reduction(), 0)
    if attack_suit == 'H' and not defender.crit_immune():  # Head: unblocked hits crit
        return land_hit(result, 'crit', int(damage * attacker.crit_multiplier()), attack_card, attacker, defender)
    return land_hit(result, 'hit', damage, attack_card, attacker, defender)


def land_hit(result, outcome, damage, attack_card, attacker, defender):
    damage = max(damage - defender.damage_reduction(), 0)
    result.update(outcome=outcome, damage=damage, attacker_heal=attacker.attack_heal(attack_card, damage))
    return result


class Game:
    def __init__(self, player_A, player_B):
        """Players keep their HP, items and class between duels, so a run can reuse them."""
        self.deck = CardDeck()
        self.discard_pile = []
        self.player_A = player_A
        self.player_B = player_B
        self.player_A.prepare_for_duel()
        self.player_B.prepare_for_duel()

        self.turn_counter = 1
        self.game_over = False
        self.winner = None

        self.refill_hand(self.player_A)
        self.refill_hand(self.player_B)

    def get_current_turn(self):
        """Resolve initiative based on turn counter."""
        self.player_A.initiative = self.turn_counter % 2
        self.player_B.initiative = (self.turn_counter + 1) % 2

        if self.player_A.initiative > self.player_B.initiative:
            return self.player_A, self.player_B
        else:
            return self.player_B, self.player_A

    def draw_card(self):
        """Draw from the deck, reshuffling the discard pile back in when the deck runs out."""
        if not self.deck.deck:
            self.deck.put_cards_in_deck(self.discard_pile)
            self.discard_pile = []
        return self.deck.pull_out_random_card()

    def refill_hand(self, player):
        while len(player.hand) < player.hand_limit():
            card = self.draw_card()
            if card is None:
                break
            player.hand.append(card)
        player.hand_size_modifier = 0

    def opponent_of(self, player):
        return self.player_B if player is self.player_A else self.player_A

    def unseen_cards(self, player):
        """Every card this player can't see: the deck plus the opponent's hand."""
        known = set(player.hand) | set(self.discard_pile)
        return [card for card in itertools.product(CARD_RANKS, CARD_SUITS) if card not in known]

    def possible_opponent_cards(self, player):
        """What the opponent might play: their exact hand when it's been revealed, otherwise every unseen card."""
        if player.sees_opponent_hand():
            return list(self.opponent_of(player).hand)
        return self.unseen_cards(player)

    def use_active(self, player, attacking):
        """Use the player's active skill before cards are chosen. Returns what happened, or None if unavailable."""
        if not player.character.can_use_active(player, attacking):
            return None
        return player.character.use_active(self, player, self.opponent_of(player))

    def usable_items(self, player, attacking):
        if player.used_item_this_turn:
            return []
        return [item for item in player.consumables if item.can_use(attacking)]

    def use_item(self, player, item, attacking):
        """Use one consumable before cards are chosen (one per turn). Returns what happened, or None if not allowed."""
        if item not in self.usable_items(player, attacking):
            return None
        player.consumables.remove(item)
        player.used_item_this_turn = True
        if item.arms:
            player.armed_items.append(item)
        return item.use(self, player, self.opponent_of(player))

    def play_clash(self, attacker, defender, attack_card, defence_card):
        """Both cards must have been chosen blind. defence_card=None means the defender braces."""
        if defence_card is None and not defender.can_brace():
            raise ValueError(f"{defender.name} can't brace")

        attacker.play_card(attack_card)
        self.discard_pile.append(attack_card)
        if defence_card is None:
            defender.hand_size_modifier += 1  # kept the card and draws one extra
        else:
            defender.play_card(defence_card)
            self.discard_pile.append(defence_card)

        result = resolve_clash(attack_card, defence_card, attacker, defender)
        defender.remove_hp(result['damage'])
        attacker.remove_hp(result['counter_damage'])
        attacker.heal(result['attacker_heal'])
        defender.heal(result['defender_heal'])
        defender.character.on_damage_taken(result['damage'])
        attacker.character.on_damage_taken(result['counter_damage'])

        result.update(attack_card=attack_card, defence_card=defence_card, effect=None, lost_card=None)
        if result['damage'] > 0 and attack_card[1] == 'C' and not defender.ignores_slow():  # Legs: slowed
            defender.hand_size_modifier -= 1
            result['effect'] = 'slowed'
        elif result['damage'] > 0 and attack_card[1] == 'S':  # Arms: disarmed
            lost_card = defender.discard_random_card()
            if lost_card:
                self.discard_pile.append(lost_card)
                result.update(effect='disarmed', lost_card=lost_card)

        attacker.end_clash()
        defender.end_clash()

        # Last strike: the game is only decided at the end of a round, so a player who
        # falls to the first attack of a round still gets to hit back
        if self.is_round_complete() and min(self.player_A.hp, self.player_B.hp) <= 0:
            self.game_over = True
            if self.player_A.hp > self.player_B.hp:
                self.winner = self.player_A.name
            elif self.player_B.hp > self.player_A.hp:
                self.winner = self.player_B.name

        return result

    def is_round_complete(self):
        """A round is two turns, so each player has attacked once."""
        return self.turn_counter % 2 == 0

    def is_last_strike(self):
        """True when someone has fallen but the round isn't over, so the fallen player strikes back."""
        return not self.game_over and min(self.player_A.hp, self.player_B.hp) <= 0

    def advance_turn(self):
        attacker, defender = self.get_current_turn()
        self.refill_hand(attacker)
        self.refill_hand(defender)
        for player in (attacker, defender):
            player.character.tick_cooldown()
            player.used_item_this_turn = False
        self.turn_counter += 1

    def is_game_over(self):
        return self.game_over

    def get_winner(self):
        return self.winner
