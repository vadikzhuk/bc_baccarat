import random
from ai_opponent import choose_loadout
from class_character import CHARACTER_CLASSES
from class_item import ITEM_CLASSES, STARTING_GOLD, slot_problem
from class_player import Player

FLOORS = 6
ENEMY_TITLES = ["Brawler", "Raider", "Veteran", "Elite", "Warlord", "Champion"]
ENEMY_BASE_GOLD = 0          # enemy loadout budget on floor 1
ENEMY_GOLD_PER_FLOOR = 2
ENEMY_HP_FLOOR_1 = -22       # added to the enemy class's max HP on floor 1 (negative = weaker)
ENEMY_HP_PER_FLOOR = 3
BOSS_HP_BONUS = 8
AFTER_FIGHT_HEAL = 0.6       # share of missing HP healed after every win

WIN_GOLD = 5                 # plus the floor number
SHOP_STOCK_SIZE = 6          # random items on offer after each win; the first shop has everything
REWARD_CHOICES = 3
REST_HEAL = 15
TRAIN_MAX_HP = 6
LOOT_GOLD = 6


class Run:
    """A climb through FLOORS duels. HP, items and gold carry over; lose once and the run is over."""

    def __init__(self, hero_name, hero_class):
        self.hero = Player(hero_name, hero_class())
        self.gold = STARTING_GOLD
        self.floor = 1
        self.shop_stock = list(ITEM_CLASSES)

    def is_final_floor(self):
        return self.floor == FLOORS

    def make_enemy(self):
        enemy_class = random.choice(CHARACTER_CLASSES)
        budget = ENEMY_BASE_GOLD + ENEMY_GOLD_PER_FLOOR * (self.floor - 1)
        enemy = Player(ENEMY_TITLES[self.floor - 1], enemy_class(), [item() for item in choose_loadout(budget, enemy_class)])
        enemy.max_hp_bonus = (ENEMY_HP_FLOOR_1 + ENEMY_HP_PER_FLOOR * (self.floor - 1)
                              + (BOSS_HP_BONUS if self.is_final_floor() else 0))
        enemy.hp = enemy.max_hp()
        return enemy

    def win_fight(self):
        """Pay out for a won duel and move up a floor. Returns the gold earned."""
        self.hero.hp = max(self.hero.hp, 1)  # won on overkill tiebreak: barely standing
        self.hero.heal(int((self.hero.max_hp() - self.hero.hp) * AFTER_FIGHT_HEAL))
        earned = WIN_GOLD + self.floor
        self.gold += earned
        self.floor += 1
        self.shop_stock = random.sample(ITEM_CLASSES, SHOP_STOCK_SIZE)
        return earned

    # Rewards: pick one of a few after each win
    def reward_options(self):
        """Returns (kind, label, apply) tuples; call apply() for the one picked."""
        hero = self.hero
        options = [
            ('rest', f"Rest: heal {REST_HEAL} HP", lambda: hero.heal(REST_HEAL)),
            ('train', f"Train: +{TRAIN_MAX_HP} max HP", self.train),
            ('loot', f"Loot: +{LOOT_GOLD} gold", lambda: self.add_gold(LOOT_GOLD)),
        ]
        carryable = [item for item in ITEM_CLASSES if slot_problem(self.owned_items() + [item]) is None]
        if carryable:
            found = random.choice(carryable)
            options.append(('find', f"Find: {found.name} - {found.description}", lambda: self.take_item(found)))
        if hero.character.active_cooldown > 1:
            options.append(('master', f"Master {hero.character.active_name}: cooldown -1", self.master_skill))
        return random.sample(options, min(REWARD_CHOICES, len(options)))

    def train(self):
        self.hero.max_hp_bonus += TRAIN_MAX_HP
        self.hero.heal(TRAIN_MAX_HP)

    def add_gold(self, amount):
        self.gold += amount

    def master_skill(self):
        self.hero.character.active_cooldown -= 1

    # Shop
    def owned_items(self):
        return self.hero.equipment + self.hero.consumables

    def replaced_by(self, item):
        """The equipped item a new weapon or armor would replace, if any."""
        if item.slot == 'consumable':
            return None
        return next((owned for owned in self.hero.equipment if owned.slot == item.slot), None)

    def sell_price(self, item):
        return item.price // 2

    def buy_problem(self, item):
        """Why this item can't be bought, or None. Buying a weapon or armor sells the one it replaces."""
        replaced = self.replaced_by(item)
        refund = self.sell_price(replaced) if replaced else 0
        if item.price > self.gold + refund:
            return "not enough gold"
        kept = [owned for owned in self.owned_items() if owned is not replaced]
        return slot_problem(kept + [item])

    def buy(self, item):
        replaced = self.replaced_by(item)
        if replaced:
            self.sell(replaced)
        self.gold -= item.price
        self.shop_stock.remove(item)
        self.take_item(item)

    def sell(self, item):
        self.gold += self.sell_price(item)
        if item.slot == 'consumable':
            self.hero.consumables.remove(item)
        else:
            self.hero.equipment.remove(item)
            self.hero.hp = min(self.hero.hp, self.hero.max_hp())

    def take_item(self, item_class):
        item = item_class()
        if item.slot == 'consumable':
            self.hero.consumables.append(item)
        else:
            self.hero.equipment.append(item)
            self.hero.hp += item.hp_bonus  # new max HP comes filled
