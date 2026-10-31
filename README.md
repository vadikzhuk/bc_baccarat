# Card Duel

A fantasy card-duelling roguelike. You and a rival each hold five cards from a standard 52-card deck. One of you attacks and the other defends: both pick a card face-down, and the rank and suit decide whether the blow is parried, blocked or lands.

Six classes bend the rules in their own ways. Items let you shape your build. **The Climb** strings six duels together into a run with persistent HP, gold, rewards and a shop.

The game has a mouse-driven pygame front-end in minimalist pixel art, plus a console version and a bot-vs-bot simulator used for balancing.

## Quick start

You need Python 3.9 or newer and [pygame](https://www.pygame.org/) 2.x.

```bash
pip install pygame
```

Start the game with:

```bash
python pygame_front.py
```

Other entry points:

| Command | What it does |
|---|---|
| `python pygame_front.py` | The game: menu, Quick Duel and The Climb |
| `python play_console.py` | A single duel in the terminal |
| `python play_run.py` | The Climb in the terminal |
| `python simulate.py [games]` | Bot-vs-bot statistics: AI strength, class match-ups, run clear rates |
| `python make_pixel_art.py` | Regenerates the portraits and backgrounds in `assets/` |

The UI uses the macOS fonts Luminari (titles) and Silom (text). On other systems it falls back to pygame's default font. The game still works, but it looks less fantasy.

## Rules

### The cards

Each card is an attack or a defence, and it tells you two things:

- **Rank = strength.** 2–10 count as printed, J = 11, Q = 12, K = 13, A = 14.
- **Suit = body zone.** The zone decides what happens when the card hits.

| Suit | Zone | Special effect when an attack with this suit gets through |
|---|---|---|
| ♥ | Head | **Critical hit.** An unblocked Head hit deals ×1.5 damage. |
| ♦ | Body | **Hard to block.** A block can at most halve the damage. |
| ♣ | Legs | **Slow.** The defender draws 1 card fewer at the next refill. |
| ♠ | Arms | **Disarm.** The defender loses a random card from their hand. |

Legs and Arms trigger only when the hit deals more than 0 damage.

### Hand and deck

- Everyone starts a duel with 5 cards. Hands refill to the limit at the end of every turn.
- Played cards go face-up to the discard pile, so you can count what is left. When the deck runs out, the discard pile is shuffled back in.
- Your opponent's hand is hidden unless an effect reveals it.

### A turn

Players take turns attacking. You attack on turn 1, and **a round** is two turns, one attack each.

1. **Preparation.** The attacker may use their class skill and one consumable item. These are announced openly. Then the defender sees them and may react with their own skill and item.
2. **Blind pick.** Both players choose a card face-down at the same time. The defender may instead **brace**, playing no card at all.
3. **Reveal.** The two cards are compared and damage is dealt (see the next section).
4. **Refill.** Both hands refill, skill cooldowns tick down by 1, and the next turn starts with the roles swapped.

The AI follows the same rules. It only sees its own hand and the discard pile, never your pick.

### What the clash does

The game checks these steps from the top and stops at the first one that matches:

1. **Parry: same rank.**
   - The defender takes no damage.
   - The attacker takes half the attack value back, rounded down.
   - Only printed ranks are compared; bonuses don't count. With a Monk or a Rapier, ranks within 1 also parry (a 7 parries 6, 7 or 8).
2. **Block: same suit.**
   - Damage = attack value − defence rank, never below 0.
   - Against a ♦ Body attack, the block can only halve the damage, rounded up.
3. **Hit: anything else**, including a brace.
   - The attack lands for its full value.
   - On ♥ Head it becomes a critical hit.

### Bracing

Instead of playing a card, the defender can brace:

- They take the attack as an unblocked hit, so a ♥ attack crits.
- They keep the card they would have played, and draw **1 extra card** at the next refill.

Bracing lets you save a strong hand or dig for better cards. Barbarians can't brace.

### Damage order

The full calculation, with classes and items included:

1. **Attack value** = card rank + attack bonuses: Greataxe +3, Whetstone +4, Barbarian's Unleash +2 per rage.
2. **Parry?** The defender's rank is within the parry window of the attack's rank (0 normally, 1 with Monk or Rapier). Then:
   - The defender takes 0.
   - The attacker takes `attack value ÷ 2` (rounded down), minus their own Chainmail.
   - The clash ends here.
3. **Block?** The suits match, or the defender has Divine Shield or a Buckler, and the attack isn't an Iron Palm. Then:
   - Damage = `attack value − defence rank`, never below 0.
   - If the attack is ♦ or the attacker has a War Hammer, damage is at least half the attack value, rounded up.
4. **Otherwise it's a hit.** Start from the attack value, then apply, in this order:
   - Rogue +4.
   - Boots −4 if the defender braced.
   - ×1.5 on ♥ Head (×2 for an Assassin), rounded down. No multiplier if the defender wears a Helm.
5. **Armor.** Chainmail takes 2 off any damage that gets through.
6. **Afterwards:**
   - Heals happen: Warlock life drain, Paladin ♥ defence.
   - Zone effects trigger if damage was above 0: ♣ slow, ♠ disarm.
   - A Barbarian who took damage gains rage.

Healing never takes you above your max HP. Damage can take HP below 0, which matters for breaking ties.

**Examples**

| Attack | Defence | Result |
|---|---|---|
| K♥ | 7♣ | Different suit → 13, Head crit ×1.5 → **19** |
| 10♠ | 6♠ | Block → 10 − 6 = **4**, and the defender loses a random card |
| Q♦ | K♦ | Block → 12 − 13 = 0, but a Body block can only halve → **6** |
| 9♣ | 9♥ | Parry → the defender takes 0, the attacker takes **4** |
| Assassin A♥ + Whetstone | Brace, wearing Boots and Chainmail | 14 + 4 = 18 → Boots −4 = 14 → ×2 = 28 → Chainmail −2 → **26** |

### Winning: the last strike

- **The duel is only decided at the end of a round.** If you fall to the first attack of a round, you still get your attack back: the **last strike**.
- After the round, if anyone is at 0 HP or below, the player with **more HP wins**. If both fell, the one with less overkill wins.
- Equal HP is a draw. In The Climb, a draw ends your run.

### Classes

Each class has a **passive** that bends one rule and an **active skill**. A skill's timing says whether it can be used when attacking, when defending, or either. Cooldowns count turns, and both players' attacks count.

| Class | HP | Passive | Active skill |
|---|---|---|---|
| **Barbarian** | 54 | **Rage.** +1 rage (max 5) every time you take damage. Can't brace. | **Unleash** (attack, needs rage): spend all rage for +2 damage per rage on this attack. |
| **Rogue** | 52 | **Backstab.** Unblocked hits deal +4 damage. | **Pickpocket** (any, cooldown 3): steal a random card from the opponent's hand. |
| **Assassin** | 50 | Unblocked ♥ Head hits deal ×2 instead of ×1.5. | **Mark** (any, cooldown 2): see the opponent's whole hand this turn. |
| **Paladin** | 45 | Defending with a ♥ card heals you for ⅓ of its rank, whatever the outcome. | **Divine Shield** (defend, cooldown 6): your defence card blocks any suit this turn. |
| **Monk** | 42 | Parry when ranks are within 1 of each other. | **Iron Palm** (attack, cooldown 4): this attack can't be blocked, only parried. |
| **Warlock** | 58 | **Life drain.** Every hit heals you for ⅓ of the damage dealt. | **Blood Pact** (any, cooldown 2): pay 3 HP, draw 2 cards. |

### Items

You carry **one weapon, one armor and up to three consumables**.

- Weapons and armor work for the whole duel.
- Consumables are used during the preparation step, at most one per turn, and each is used once.
- In a Quick Duel you shop with **10 gold**.

| Item | Slot | Price | Effect |
|---|---|---|---|
| Rapier | weapon | 5g | Parry when ranks are within 1. Doesn't stack with the Monk's passive. |
| Greataxe | weapon | 4g | +3 damage on every attack, but you hold one card fewer. |
| War Hammer | weapon | 2g | A block can at most halve your damage, whatever the suit. |
| Helm | armor | 2g | ♥ Head hits against you never crit. |
| Chainmail | armor | 5g | Every clash hit against you deals 2 less damage. |
| Padded Vest | armor | 3g | +8 max HP. |
| Boots | armor | 3g | Bracing takes 4 off the hit, and ♣ Legs hits never slow you. |
| Healing Potion | consumable | 3g | Heal 8 HP. |
| Whetstone | consumable (attack) | 1g | +4 damage on this attack. |
| Buckler | consumable (defend) | 1g | Your defence card blocks any suit this turn. |
| Smoke Bomb | consumable | 2g | Discard your hand and draw the same number of new cards. |
| Throwing Knife | consumable | 2g | Deal 5 damage right now. It can't be blocked or reduced by armor. |

### Game modes

**Quick Duel**: one fight against an AI rival.
1. Pick your class.
2. Shop with 10 gold.
3. Fight a rival of a random class, who also shops with 10 gold.

**The Climb**: beat six opponents in a row. The opponents are, in order: Brawler, Raider, Veteran, Elite, Warlord and the Champion.
- Lose once and the run is over.
- **Carried over between fights:** your HP, max HP, items and gold. Skill cooldowns, rage and your hand reset every duel.
- **Enemies:** a random class.
  - They start weaker than you and grow tougher every floor, both in max HP and in the gold they spend on items.
  - The Champion on floor 6 gets extra HP.
- **After every win:**
  - You heal **60% of your missing HP**.
  - You earn **5 + floor number** gold.
  - You pick **one of three rewards**, drawn from:
    - **Rest:** heal 15 HP.
    - **Train:** +6 max HP.
    - **Loot:** +6 gold.
    - **Find:** a random item.
    - **Master:** your skill's cooldown −1.
- **Shop:**
  - The first shop sells everything. Later shops offer 6 random items.
  - You sell items for half their price.
  - Buying a weapon or armor automatically sells the one it replaces.

## Project layout

| File | Contents |
|---|---|
| `constants.py` | Card ranks, zones and base duel numbers |
| `class_card_deck.py` | The 52-card deck |
| `class_character.py` | `Modifier` rule hooks, `Character` and the six classes |
| `class_item.py` | Weapons, armor and consumables, plus loadout and slot checks |
| `class_player.py` | `Player`: HP, hand and equipment; combines the hooks of class, gear and armed items |
| `game_backend.py` | `resolve_clash` (all damage math) and `Game` (turns, drawing, skills, items, win check) |
| `ai_opponent.py` | The AI: expected-value scoring with weighted randomness, plus shop and reward choices |
| `class_run.py` | `Run`: The Climb, with enemy scaling, rewards and shop |
| `duel_text.py` | Rules text and log lines shared by the console and pygame front-ends |
| `pygame_front.py` | The pygame game: scenes, pixel fonts, framed panels |
| `play_console.py`, `play_run.py` | Terminal versions |
| `simulate.py` | Bot-vs-bot balancing statistics |
| `make_pixel_art.py` | Generates the class portraits (male and female) and backgrounds |

Every rule bend is a hook on `Modifier`. A new class or item just overrides the hooks it changes. `resolve_clash` is the single place damage is calculated, and the AI uses it too when scoring its options.

## License

Released under the [MIT License](LICENSE).
