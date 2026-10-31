from class_item import MAX_CONSUMABLES
from class_run import AFTER_FIGHT_HEAL, FLOORS, Run
from game_backend import Game
from play_console import RULES, ask_class, describe_class, gear_line, play_duel

RUN_RULES = f"""
THE CLIMB - beat {FLOORS} opponents in a row, the last one a champion.
Your HP, items and gold carry over between fights; lose once and the run is over.
After each win: gold, {AFTER_FIGHT_HEAL:.0%} of missing HP back, one reward of your choice, and a shop visit.
"""


def run_status(run):
    hero = run.hero
    return f"Floor {run.floor}/{FLOORS} | {hero.hp}/{hero.max_hp()} HP | {run.gold} gold"


def shop(run):
    """Buy by number, sell owned items with s<number>, Enter to leave. Buying gear replaces (and sells) the old piece."""
    while True:
        print(f"\n--- Shop | {run_status(run)} | one weapon, one armor, up to {MAX_CONSUMABLES} consumables ---")
        print(gear_line(run.hero))
        for number, item in enumerate(run.shop_stock, start=1):
            print(f"   {number}) {item.name:<15} {item.slot:<10} {item.price}g  {item.description}")
        owned = run.owned_items()
        if owned:
            print("   Sell: " + '  '.join(f"s{number}) {item.name} +{run.sell_price(item)}g"
                                       for number, item in enumerate(owned, start=1)))

        answer = input("Buy [number], sell [s+number], Enter to leave: ").strip().lower()
        if not answer:
            return
        selling = answer.startswith('s')
        number = answer.lstrip('s')
        choices = owned if selling else run.shop_stock
        if not number.isdigit() or not 1 <= int(number) <= len(choices):
            print("  Not a valid choice.")
            continue
        item = choices[int(number) - 1]
        if selling:
            run.sell(item)
            continue
        problem = run.buy_problem(item)
        if problem:
            print(f"  Can't buy {item.name}: {problem}.")
            continue
        replaced = run.replaced_by(item)
        run.buy(item)
        print(f"  Bought {item.name}" + (f", sold {replaced.name}." if replaced else "."))


def ask_reward(run):
    options = run.reward_options()
    print("\nChoose a reward:")
    for number, (kind, label, apply) in enumerate(options, start=1):
        print(f"   {number}) {label}")
    while True:
        answer = input(f"Choose [1-{len(options)}]: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            options[int(answer) - 1][2]()
            return
        print("  Not a valid choice.")


def main():
    print(RULES)
    print(RUN_RULES)
    run = Run("Hero", ask_class())
    shop(run)

    while True:
        enemy = run.make_enemy()
        title = "FINAL FIGHT" if run.is_final_floor() else f"Floor {run.floor}"
        print(f"\n################ {title}: {enemy.name} ################")
        print(f"{run_status(run)}")
        print(f"Your opponent: {describe_class(type(enemy.character))}")
        print(f"      {enemy.max_hp()} HP this fight")
        print(gear_line(enemy))
        input("[Enter] fight")

        if not play_duel(Game(run.hero, enemy)):
            print(f"\nYour run ends on floor {run.floor} of {FLOORS}.")
            return
        if run.is_final_floor():
            print(f"\nYou beat the {enemy.name} and conquer the climb! Run cleared with {run.hero.hp} HP left.")
            return

        earned = run.win_fight()
        print(f"\nVictory! +{earned} gold. You catch your breath. {run_status(run)}")
        ask_reward(run)
        shop(run)


if __name__ == "__main__":
    main()
