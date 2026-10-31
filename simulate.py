"""Bot-vs-bot runs for balance checks: python simulate.py [games]"""
import sys
from collections import Counter
import ai_opponent
from ai_opponent import choose_loadout
from class_character import CHARACTER_CLASSES, Character
from class_run import FLOORS, Run
from class_player import Player
from game_backend import Game

TURN_LIMIT = 200

SMART = (ai_opponent.choose_attack, ai_opponent.choose_defence)
RANDOM = (ai_opponent.choose_attack_random, ai_opponent.choose_defence_random)


def play_game(bot_A, bot_B, class_A=Character, class_B=Character, items_A=(), items_B=()):
    game = Game(Player("A", class_A(), [item() for item in items_A]),
                Player("B", class_B(), [item() for item in items_B]))
    return play_duel(game, bot_A, bot_B)


def play_duel(game, bot_A, bot_B):
    bots = {game.player_A.name: bot_A, game.player_B.name: bot_B}
    outcomes = Counter()
    while not game.is_game_over() and game.turn_counter <= TURN_LIMIT:
        attacker, defender = game.get_current_turn()
        for player, attacking in ((attacker, True), (defender, False)):
            if bots[player.name] is SMART and ai_opponent.wants_active(player):
                game.use_active(player, attacking)
            if bots[player.name] is SMART:
                item = ai_opponent.choose_item(game.usable_items(player, attacking), player)
                if item:
                    game.use_item(player, item, attacking)
        attack_card = bots[attacker.name][0](attacker.hand, game.possible_opponent_cards(attacker), attacker, defender)
        defence_card = bots[defender.name][1](defender.hand, game.possible_opponent_cards(defender), defender, attacker)
        result = game.play_clash(attacker, defender, attack_card, defence_card)
        outcomes[result['outcome'] if defence_card else 'brace'] += 1
        game.advance_turn()
    return game.get_winner(), game.turn_counter - 1, outcomes


def run(label, bot_A, bot_B, games, class_A=Character, class_B=Character):
    wins, turns, outcomes = Counter(), [], Counter()
    for _ in range(games):
        winner, turn_count, game_outcomes = play_game(bot_A, bot_B, class_A, class_B)
        wins[winner] += 1
        turns.append(turn_count)
        outcomes += game_outcomes
    total_clashes = sum(outcomes.values())
    outcome_share = ', '.join(f"{name} {count / total_clashes:.0%}" for name, count in outcomes.most_common())
    print(f"{label}: A wins {wins['A'] / games:.0%}, B wins {wins['B'] / games:.0%}, "
          f"no winner {wins[None] / games:.0%} | avg {sum(turns) / games:.1f} turns | {outcome_share}")


def class_matchups(games):
    """Win rate of each row class against each column class, both seat orders, smart bots with random shop loadouts."""
    print(f"\nClass matchups (row's win rate vs column, {games} games per seat order):")
    print(" " * 10 + "".join(f"{cls.name[:9]:>10}" for cls in CHARACTER_CLASSES) + "   overall")
    for row in CHARACTER_CLASSES:
        cells, row_wins, row_games = [], 0, 0
        for column in CHARACTER_CLASSES:
            wins = 0
            for _ in range(games):
                wins += play_game(SMART, SMART, row, column, choose_loadout(character_class=row),
                                  choose_loadout(character_class=column))[0] == 'A'
                wins += play_game(SMART, SMART, column, row, choose_loadout(character_class=column),
                                  choose_loadout(character_class=row))[0] == 'B'
            cells.append(f"{wins / (2 * games):>10.0%}")
            if column is not row:
                row_wins, row_games = row_wins + wins, row_games + 2 * games
        print(f"{row.name:<10}" + "".join(cells) + f"{row_wins / row_games:>10.0%}")


def play_run(hero_class):
    """A smart bot climbs a run. Returns the floor it fell on, or FLOORS + 1 for a cleared run."""
    run = Run("Hero", hero_class)
    ai_opponent.shop_in_run(run)
    while True:
        winner = play_duel(Game(run.hero, run.make_enemy()), SMART, SMART)[0]
        if winner != run.hero.name:
            return run.floor
        if run.is_final_floor():
            return FLOORS + 1
        run.win_fight()
        ai_opponent.choose_reward(run.reward_options(), run.hero)[2]()
        ai_opponent.shop_in_run(run)


def run_stats(runs):
    """How far a smart bot gets with each class."""
    print(f"\nRuns ({runs} per class): share of runs that reach each floor")
    print(" " * 10 + "".join(f"{f'F{floor}':>6}" for floor in range(2, FLOORS + 1)) + "   cleared")
    for hero_class in CHARACTER_CLASSES:
        results = Counter(play_run(hero_class) for _ in range(runs))
        reached = [sum(count for fell_on, count in results.items() if fell_on >= floor) / runs
                   for floor in range(2, FLOORS + 2)]
        print(f"{hero_class.name:<10}" + "".join(f"{share:>6.0%}" for share in reached[:-1]) + f"{reached[-1]:>10.0%}")


if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    run("smart vs smart  ", SMART, SMART, games)
    run("smart vs random ", SMART, RANDOM, games)
    run("random vs smart ", RANDOM, SMART, games)
    run("random vs random", RANDOM, RANDOM, games)
    class_matchups(games // 4)
    run_stats(games // 10)
