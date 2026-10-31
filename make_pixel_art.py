"""Generates the pixel-art assets: a male and a female portrait for every class, and the screen backgrounds.
Everything is drawn from code on a small grid and scaled up with hard pixel edges.
Re-run after changing anything here: ../venv/bin/python make_pixel_art.py
"""
import os
import random
import pygame

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
PORTRAIT_DIR = os.path.join(ASSET_DIR, 'portraits')
BACKGROUND_DIR = os.path.join(ASSET_DIR, 'backgrounds')

GRID = 40            # portrait is drawn on a 40x40 grid...
SCALE = 5            # ...and saved at 200x200
BACKDROP = (216, 213, 199)
FLOOR_SHADOW = (198, 194, 180)
OUTLINE = (38, 28, 32)

# Shared colors
SKIN_LIGHT = (236, 192, 152)
SKIN_TAN = (204, 146, 100)
SKIN_DARK = (158, 104, 72)
SKIN_PALE = (204, 194, 204)
EYE = (40, 30, 40)
LIPS = (184, 76, 80)
LEATHER = (124, 82, 50)
LEATHER_DARK = (88, 56, 36)
WOOD = (132, 88, 52)
STEEL = (176, 182, 194)
STEEL_DARK = (124, 130, 146)
STEEL_LIGHT = (226, 230, 238)
GOLD = (226, 182, 64)
FUR = (164, 122, 76)
FUR_DARK = (120, 86, 52)
IVORY = (234, 224, 194)


def shade(color, factor):
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


class Sprite:
    """A grid of colored pixels. finish() adds outline, edge shading and the floor shadow."""

    def __init__(self):
        self.pixels = {}
        self.flat = set()  # pixels that keep their exact color (eyes, glows)

    def put(self, x, y, color, flat=False):
        if 0 <= x < GRID and 0 <= y < GRID:
            self.pixels[(x, y)] = color
            if flat:
                self.flat.add((x, y))
            else:
                self.flat.discard((x, y))

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, color)

    def stamp(self, rows, x0, y0, palette, flat_keys=''):
        """rows: strings where each character is a palette key, '.' leaves the pixel alone."""
        for dy, row in enumerate(rows):
            for dx, key in enumerate(row):
                if key != '.':
                    self.put(x0 + dx, y0 + dy, palette[key], flat=key in flat_keys)

    def finish(self):
        image = pygame.Surface((GRID, GRID))
        image.fill(BACKDROP)
        for x in range(10, 30):
            image.set_at((x, 38), FLOOR_SHADOW)
        for x in range(13, 27):
            image.set_at((x, 39), FLOOR_SHADOW)

        # Light from the left: darken right silhouette edges, brighten left ones
        for (x, y), color in self.pixels.items():
            if (x, y) not in self.flat:
                if (x + 1, y) not in self.pixels:
                    color = shade(color, 0.76)
                elif (x - 1, y) not in self.pixels:
                    color = shade(color, 1.12)
            image.set_at((x, y), color)

        for y in range(GRID):
            for x in range(GRID):
                if (x, y) not in self.pixels and any(
                        (x + dx, y + dy) in self.pixels for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    image.set_at((x, y), OUTLINE)
        return pygame.transform.scale(image, (GRID * SCALE, GRID * SCALE))


# ---------- body ----------

class Body:
    """Where each body part sits on the grid. Rows are inclusive; x ranges are (left, right)."""

    def __init__(self, female):
        self.female = female
        if female:
            self.torso = {15: (14, 25), 16: (14, 25)}
            self.torso.update({y: (15, 24) for y in range(17, 21)})
            self.torso.update({y: (16, 23) for y in range(21, 24)})
            self.torso.update({y: (15, 24) for y in range(24, 27)})
            self.arms = ((12, 13), (26, 27))
            self.legs = ((16, 18), (21, 23))
            self.feet = ((15, 18), (21, 24))
            self.legs_from = 27
        else:
            self.torso = {y: (13, 26) for y in range(15, 18)}
            self.torso.update({y: (14, 25) for y in range(18, 22)})
            self.torso.update({y: (15, 24) for y in range(22, 25)})
            self.arms = ((11, 12), (27, 28))
            self.legs = ((15, 18), (21, 24))
            self.feet = ((14, 18), (21, 25))
            self.legs_from = 25

    @property
    def right_hand_x(self):
        return self.arms[1][0]

    @property
    def left_hand_x(self):
        return self.arms[0][0]

    def fill_torso(self, sprite, color, y0=15, y1=26):
        for y, (x0, x1) in self.torso.items():
            if y0 <= y <= y1:
                sprite.rect(x0, y, x1, y, color)

    def fill_arms(self, sprite, color, y0=16, y1=24):
        for x0, x1 in self.arms:
            sprite.rect(x0, y0, x1, y1, color)

    def fill_hands(self, sprite, color):
        for x0, x1 in self.arms:
            sprite.rect(x0, 25, x1, 26, color)

    def fill_legs(self, sprite, color, y0=None, y1=34):
        for x0, x1 in self.legs:
            sprite.rect(x0, y0 or self.legs_from, x1, y1, color)

    def fill_feet(self, sprite, color):
        for x0, x1 in self.feet:
            sprite.rect(x0, 35, x1, 36, color)

    def draw_base(self, sprite, skin):
        sprite.rect(16, 6, 23, 13, skin)       # head, with rounded corners
        for corner in ((16, 6), (23, 6), (16, 13), (23, 13)):
            del sprite.pixels[corner]
        sprite.rect(18, 14, 21, 14, skin)      # neck
        self.fill_torso(sprite, skin)
        self.fill_arms(sprite, skin)
        self.fill_hands(sprite, skin)
        self.fill_legs(sprite, skin)
        self.fill_feet(sprite, skin)

    def draw_face(self, sprite, skin, eye=EYE, mouth=True, glow=False):
        sprite.put(18, 9, eye, flat=True)
        sprite.put(21, 9, eye, flat=True)
        if self.female and not glow:
            sprite.put(17, 8, EYE, flat=True)   # lashes
            sprite.put(22, 8, EYE, flat=True)
        if mouth:
            mouth_color = LIPS if self.female else shade(skin, 0.72)
            sprite.put(19, 11, mouth_color, flat=True)
            sprite.put(20, 11, mouth_color, flat=True)


HEAD_X, HEAD_Y = 13, 3   # head stamps are 14 wide and start here; the face sits at stamp columns 3-10


# ---------- classes ----------

def barbarian(female):
    body, sprite = Body(female), Sprite()
    hair = (166, 74, 38)
    body.draw_base(sprite, SKIN_TAN)
    if female:
        body.fill_torso(sprite, FUR, 17, 19)                     # fur top
        sprite.rect(14, 15, 17, 16, FUR)                         # shoulder pelt
        body.fill_torso(sprite, LEATHER_DARK, 23, 23)            # belt
        sprite.rect(19, 23, 20, 23, GOLD)
        body.fill_torso(sprite, FUR, 24, 26)                     # fur kilt
        for x in range(15, 25, 2):
            sprite.put(x, 27, FUR_DARK)
    else:
        for x in range(12, 28):                                  # fur mantle with ragged edge
            sprite.rect(x, 15, x, 16 + (x % 2), FUR)
        sprite.rect(16, 19, 18, 19, shade(SKIN_TAN, 0.85))      # chest
        sprite.rect(21, 19, 23, 19, shade(SKIN_TAN, 0.85))
        body.fill_torso(sprite, LEATHER_DARK, 23, 24)
        sprite.rect(19, 23, 20, 24, GOLD)
        sprite.rect(14, 25, 25, 28, FUR)
        for x in range(14, 26, 2):
            sprite.put(x, 29, FUR_DARK)
    body.fill_legs(sprite, FUR_DARK, 32, 34)                     # fur boots
    body.fill_feet(sprite, FUR_DARK)
    body.draw_face(sprite, SKIN_TAN, mouth=female)

    if female:
        head = ["..............",
                "....hhhhhh....",
                "...hhhhhhhh...",
                "..hhhhhhhhhh..",
                "..hbbbbbbbbh..",
                "..hh......hh..",
                "..hh......hh..",
                ".hhh......hhh.",
                ".hhh......hhh.",
                ".hhh......hhh.",
                ".hh........hh.",
                ".hh........hh.",
                "..h........h..",
                "..h........h.."]
    else:
        head = ["w............w",
                "w............w",
                "ww..mmmmmm..ww",
                ".wwmmmmmmmmww.",
                "...MMMMMMMM...",
                "...h......h...",
                "..hh......hh..",
                "..hh......hh..",
                "..hhhbkkbhhh..",
                "...hbbbbbbh...",
                "....bbbbbb....",
                "....bbbbbb....",
                ".....bbbb.....",
                "......bb......"]
    sprite.stamp(head, HEAD_X, HEAD_Y, {'h': hair, 'b': shade(hair, 0.9), 'w': IVORY, 'm': STEEL,
                                         'M': STEEL_DARK, 'k': OUTLINE}, flat_keys='k')

    axe = ["....mm....",
           "...hmmm...",
           "...hmmmm..",
           ".M.hmmmml.",
           "MM.hmmmmml",
           ".M.hmmmml.",
           "...hmmmm..",
           "...hmml...",
           "...h.ml..."]
    x = body.right_hand_x + 2
    sprite.stamp(axe, x - 3, 5, {'m': STEEL, 'M': STEEL_DARK, 'l': STEEL_LIGHT, 'h': WOOD})
    sprite.rect(x, 14, x, 33, WOOD)
    return sprite


def rogue(female):
    body, sprite = Body(female), Sprite()
    cloak, cloak_dark = (62, 112, 72), (42, 80, 52)
    for y in range(15, 32):                                      # cloak behind the body
        spread = (y - 15) // 6
        sprite.rect(12 - spread, y, 27 + spread, y, cloak_dark)
    body.draw_base(sprite, SKIN_LIGHT)
    body.fill_torso(sprite, LEATHER)
    body.fill_torso(sprite, LEATHER_DARK, 23, 23)
    sprite.put(19, 23, STEEL)
    sprite.rect(16, 24, 17, 25, LEATHER_DARK)                    # pouch
    body.fill_arms(sprite, cloak)
    body.fill_hands(sprite, LEATHER_DARK)
    body.fill_legs(sprite, (88, 72, 56))
    body.fill_legs(sprite, LEATHER_DARK, 32, 34)
    body.fill_feet(sprite, LEATHER_DARK)
    sprite.rect(19, 15, 20, 15, GOLD)                            # cloak clasp
    body.draw_face(sprite, SKIN_LIGHT)
    if not female:
        sprite.rect(18, 12, 21, 13, shade(SKIN_LIGHT, 0.82))     # stubble
        body.draw_face(sprite, SKIN_LIGHT)

    head = ["..............",
            ".....cccc.....",
            "....cccccc....",
            "...cccccccc...",
            "..cccCCCCccc..",
            "..ccC....Ccc..",
            "..cch....hcc..",
            "..cch....hcc..",
            "..cch....hcc..",
            "..ccch..hccc..",
            ".cccc....cccc.",
            ".cccccccccccc."]
    if not female:
        head = [row.replace('h', '.') for row in head]
    sprite.stamp(head, HEAD_X, HEAD_Y, {'c': cloak, 'C': cloak_dark, 'h': (150, 74, 44)})

    x = body.right_hand_x + 2                                    # dagger raised in the right hand
    sprite.rect(x, 25, x, 26, LEATHER_DARK)
    sprite.rect(x - 1, 24, x + 1, 24, GOLD)
    sprite.rect(x, 19, x, 23, STEEL_LIGHT)
    sprite.put(x, 18, STEEL)
    return sprite


def assassin(female):
    body, sprite = Body(female), Sprite()
    black, black_dark, sash = (58, 54, 70), (36, 33, 46), (176, 44, 50)
    body.draw_base(sprite, SKIN_TAN)
    body.fill_torso(sprite, black)
    body.fill_torso(sprite, sash, 22, 23)
    sprite.rect(23, 24, 24, 28, sash)                            # sash tails
    sprite.put(24, 29, sash)
    body.fill_arms(sprite, black)
    body.fill_arms(sprite, black_dark, 22, 24)                   # wrist wraps
    body.fill_hands(sprite, black_dark)
    body.fill_legs(sprite, black)
    body.fill_feet(sprite, black_dark)
    body.fill_legs(sprite, black_dark, 32, 34)
    body.draw_face(sprite, SKIN_TAN, eye=(200, 60, 60), mouth=False)

    head = ["..............",
            ".....cccc.....",
            "....cccccc....",
            "...cccccccc...",
            "..cccCCCCccc..",
            "..ccC....Ccc..",
            "..cc......cc..",
            "..ccCCCCCCcc..",
            "..ccCCCCCCcc..",
            "..ccCCCCCCcc..",
            ".cccCCCCCCccc.",
            ".cccccccccccc."]
    sprite.stamp(head, HEAD_X, HEAD_Y, {'c': black, 'C': black_dark})
    if female:
        braid = (126, 48, 54)
        sprite.put(16, 9, braid)                                 # fringe
        sprite.put(23, 9, braid)
        sprite.rect(15, 14, 15, 22, braid)                       # braid over the shoulder
        sprite.put(15, 23, GOLD)

    for hand_x, step in ((body.right_hand_x + 2, 1), (body.left_hand_x - 1, -1)):   # curved daggers pointing down
        sprite.put(hand_x, 25, GOLD)
        sprite.rect(hand_x, 26, hand_x, 29, STEEL_LIGHT)
        sprite.put(hand_x + step, 30, STEEL)
    return sprite


def paladin(female):
    body, sprite = Body(female), Sprite()
    tabard, hair = (52, 84, 166), (214, 172, 84)
    body.draw_base(sprite, SKIN_LIGHT)
    body.fill_torso(sprite, STEEL)
    body.fill_arms(sprite, STEEL)
    body.fill_hands(sprite, STEEL_DARK)
    body.fill_legs(sprite, STEEL)
    body.fill_feet(sprite, STEEL_DARK)
    for y in range(17, 31):                                      # tabard down to a point
        width = 3 if y < 28 else 30 - y
        sprite.rect(19 - width + 1, y, 20 + width - 1, y, tabard)
    sprite.rect(19, 18, 20, 23, GOLD)                            # emblem
    sprite.rect(18, 19, 21, 19, GOLD)
    body.fill_torso(sprite, LEATHER_DARK, 24, 24)
    for x0 in (body.arms[0][0] - 1, body.arms[1][0]):            # pauldrons
        sprite.rect(x0, 14, x0 + 3, 16, STEEL_LIGHT)
        sprite.rect(x0, 17, x0 + 3, 17, GOLD)
    body.draw_face(sprite, SKIN_LIGHT)

    if female:
        head = ["..............",
                "..............",
                "....hhhhhh....",
                "...hhhhhhhh...",
                "..hggggggggh..",
                "..hh......hh..",
                "..h........h..",
                "..h........h..",
                "..hh......hh..",
                "..hh......hh..",
                "..hhh....hhh..",
                "..hhh....hhh..",
                "..hh......hh..",
                "...h......h..."]
    else:
        head = ["..............",
                "..............",
                "....hhhhhh....",
                "...hhhhhhhh...",
                "...hhhhhhhhh..",
                "...h......h...",
                "...h......h...",
                "..............",
                "...bb.kk.bb...",
                "...bbbbbbbb...",
                "....bbbbbb....",
                ".....bbbb....."]
    sprite.stamp(head, HEAD_X, HEAD_Y, {'h': hair, 'b': shade(hair, 0.8), 'g': GOLD, 'k': OUTLINE}, flat_keys='k')

    x = body.right_hand_x + 2                                    # sword raised
    sprite.rect(x, 8, x, 23, STEEL_LIGHT)
    sprite.put(x, 7, STEEL)
    sprite.rect(x - 2, 24, x + 2, 24, GOLD)
    sprite.rect(x, 25, x, 26, LEATHER_DARK)
    sprite.put(x, 27, GOLD)

    shield = ["..rrrrrr..",
              ".rbbbbbbr.",
              "rbbbggbbbr",
              "rbbbggbbbr",
              "rbggggggbr",
              "rbbbggbbbr",
              "rbbbggbbbr",
              "rbbbggbbbr",
              ".rbbggbbr.",
              ".rbbbbbbr.",
              "..rbbbbr..",
              "...rbbr...",
              "....rr...."]
    sprite.stamp(shield, body.left_hand_x - 6, 17, {'r': STEEL_LIGHT, 'b': tabard, 'g': GOLD})
    return sprite


def monk(female):
    body, sprite = Body(female), Sprite()
    robe, robe_dark, hair = (226, 136, 44), (186, 98, 34), (34, 28, 30)
    body.draw_base(sprite, SKIN_DARK)
    body.fill_torso(sprite, robe)
    for step in range(9):                                        # sash across the chest
        sprite.put(body.torso[15][0] + 2 + step, 16 + step, (150, 50, 40))
    body.fill_arms(sprite, robe, 16, 19)
    body.fill_arms(sprite, IVORY, 22, 24)                        # hand wraps
    x0, x1 = body.torso[24][0], body.torso[24][1]
    sprite.rect(x0 - 1, 25, x1 + 1, 31, robe_dark)               # robe skirt
    body.fill_legs(sprite, SKIN_DARK, 32, 34)
    body.fill_feet(sprite, LEATHER)
    for x, y in ((17, 15), (22, 15), (17, 16), (22, 16), (18, 17), (21, 17), (19, 18), (20, 18)):
        sprite.put(x, y, (96, 56, 34), flat=True)                # prayer beads
    sprite.put(19, 18, (190, 40, 40), flat=True)
    body.draw_face(sprite, SKIN_DARK)

    if female:
        head = [".....hhhh.....",
                "....hhhhhh....",
                ".....hhhh.....",
                "...hhhhhhhh...",
                "...hhhhhhhh...",
                "...h......h...",
                "...h......h..."]
        sprite.stamp(head, HEAD_X, HEAD_Y, {'h': hair})
    else:
        sprite.put(17, 7, shade(SKIN_DARK, 1.3), flat=True)      # shine on the bald head
        for x in (15, 24):                                       # ears
            sprite.rect(x, 9, x, 10, SKIN_DARK)

    x = body.right_hand_x + 2                                    # staff
    sprite.rect(x, 3, x, 37, WOOD)
    for y in (7, 8, 31, 32):
        sprite.put(x, y, IVORY)
    return sprite


def warlock(female):
    body, sprite = Body(female), Sprite()
    robe, robe_dark, glow = (86, 54, 118), (58, 36, 84), (120, 236, 130)
    body.draw_base(sprite, SKIN_PALE)
    for y in range(15, 37):                                      # robe flaring to the floor
        spread = (y - 15) // 7
        x0, x1 = body.torso.get(y, (15 - spread, 24 + spread))
        sprite.rect(min(x0, 15 - spread), y, max(x1, 24 + spread), y, robe)
    sprite.rect(19, 17, 20, 35, robe_dark)                       # front opening
    for y in (21, 25, 29, 33):
        sprite.put(19, y, glow, flat=True)                       # runes
    for x in range(12, 28):
        if (x, 36) in sprite.pixels:
            sprite.put(x, 36, GOLD)
    body.fill_arms(sprite, robe)
    for x0, x1 in body.arms:                                     # bell sleeves
        sprite.rect(x0 - 1, 22, x1 + 1, 24, robe_dark)
    body.fill_hands(sprite, SKIN_PALE)
    body.fill_torso(sprite, (60, 44, 40), 23, 23)
    body.draw_face(sprite, SKIN_PALE, eye=glow, mouth=female, glow=True)
    if not female:
        sprite.rect(19, 12, 20, 13, (30, 24, 30))                # goatee

    head = ["...w......w...",
            "...ww....ww...",
            "....wccccw....",
            "...cccccccc...",
            "..cckkkkkkcc..",
            "..cck....kcc..",
            "..cch....hcc..",
            "..cch....hcc..",
            "..cch....hcc..",
            "..ccch..hccc..",
            ".cccch..hcccc.",
            ".cccccccccccc."]
    if not female:
        head = [row.replace('h', '.') for row in head]
    sprite.stamp(head, HEAD_X, HEAD_Y, {'w': IVORY, 'c': robe, 'k': (30, 22, 40), 'h': (214, 214, 230)})

    orb = [".gg.",
           "gGgg",
           "gggg",
           ".gg."]
    x = body.left_hand_x - 2                                     # glowing orb above the left hand
    sprite.stamp(orb, x, 20, {'g': glow, 'G': (230, 255, 230)}, flat_keys='gG')
    for spark_x, spark_y in ((x - 1, 18), (x + 4, 19), (x - 2, 22)):
        sprite.put(spark_x, spark_y, glow, flat=True)
    return sprite


PORTRAITS = {'Barbarian': barbarian, 'Rogue': rogue, 'Assassin': assassin,
             'Paladin': paladin, 'Monk': monk, 'Warlock': warlock}


def portrait_path(class_name, sex):
    return os.path.join(PORTRAIT_DIR, f"{class_name.lower()}_{sex}.png")


def make_portraits():
    os.makedirs(PORTRAIT_DIR, exist_ok=True)
    for class_name, draw in PORTRAITS.items():
        for sex in ('male', 'female'):
            pygame.image.save(draw(sex == 'female').finish(), portrait_path(class_name, sex))


# ---------- backgrounds ----------

BG_SIZE = (320, 200)     # drawn at this size, saved x4 for a 1280x800 window
BG_SCALE = 4
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dither(x, y, amount):
    """True on a share of pixels given by amount (0..1), spread in an ordered pattern."""
    return BAYER[y % 4][x % 4] < amount * 16


def mix(color_a, color_b, share):
    return tuple(int(a + (b - a) * share) for a, b in zip(color_a, color_b))


def gradient(image, stops):
    """Vertical gradient through color stops, stepped and dithered rather than smooth."""
    width, height = image.get_size()
    for y in range(height):
        position = y / (height - 1) * (len(stops) - 1)
        index = min(int(position), len(stops) - 2)
        share = position - index
        for x in range(width):
            image.set_at((x, y), stops[index + 1] if dither(x, y, share) else stops[index])


def vignette(image, strength=0.55):
    width, height = image.get_size()
    for y in range(height):
        for x in range(width):
            dx, dy = (x - width / 2) / (width / 2), (y - height / 2) / (height / 2)
            darkness = max(0.0, (dx * dx + dy * dy) ** 0.5 - 0.55) * strength * 2
            if darkness > 0:
                steps = min(int(darkness * 4), 3)
                factor = 1 - 0.14 * (steps + (1 if dither(x, y, darkness * 4 - steps) else 0))
                image.set_at((x, y), shade(image.get_at((x, y))[:3], factor))


def glow(image, center, radius, color, strength=0.5):
    """Warm light around a point, dithered in rings."""
    cx, cy = center
    width, height = image.get_size()
    for y in range(max(0, cy - radius), min(height, cy + radius)):
        for x in range(max(0, cx - radius), min(width, cx + radius)):
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / radius
            if distance < 1 and dither(x, y, (1 - distance) * strength * 1.6):
                image.set_at((x, y), mix(image.get_at((x, y))[:3], color, 0.28))


def ridge(rng, width, base, roughness, smooth=3):
    heights, height = [], base
    for _ in range(width):
        height += rng.randint(-roughness, roughness)
        height = max(base - 22, min(base + 12, height))
        heights.append(height)
    return [sum(heights[max(0, x - smooth):x + smooth + 1]) // len(heights[max(0, x - smooth):x + smooth + 1])
            for x in range(width)]


def night_sky():
    rng = random.Random(3)
    image = pygame.Surface(BG_SIZE)
    width, height = BG_SIZE
    gradient(image, [(14, 12, 34), (26, 22, 58), (52, 38, 86), (104, 62, 98), (150, 90, 96)])
    for _ in range(140):
        x, y = rng.randrange(width), rng.randrange(int(height * 0.6))
        image.set_at((x, y), rng.choice([(236, 232, 210), (180, 176, 200), (120, 116, 160)]))
    for y in range(-12, 13):                                   # moon with craters
        for x in range(-12, 13):
            if x * x + y * y <= 144:
                image.set_at((252 + x, 38 + y), (236, 228, 196))
    for x, y in ((248, 34), (249, 34), (256, 41), (257, 41), (257, 42), (245, 43)):
        image.set_at((x, y), (204, 196, 170))
    glow(image, (252, 38), 40, (236, 228, 196), 0.35)

    for base, color, roughness in ((128, (58, 44, 88), 3), (150, (40, 32, 66), 2)):
        heights = ridge(rng, width, base, roughness)
        for x, top in enumerate(heights):
            for y in range(top, height):
                image.set_at((x, y), color)

    castle = (26, 22, 44)                                      # castle on the near hill
    for x0, x1, top in ((58, 74, 104), (74, 112, 120), (112, 126, 98), (88, 98, 110)):
        for x in range(x0, x1):
            for y in range(top, 160):
                image.set_at((x, y), castle)
        for x in range(x0, x1, 4):                             # crenellations
            image.set_at((x, top - 1), castle)
            image.set_at((x + 1, top - 1), castle)
    for x, y in ((65, 112), (66, 112), (118, 106), (118, 107), (92, 118), (80, 130), (100, 130), (65, 124)):
        image.set_at((x, y), (240, 196, 92))
    for x in range(width):
        for y in range(176, height):
            image.set_at((x, y), (20, 16, 32))
    return image


def stone_wall():
    rng = random.Random(5)
    image = pygame.Surface(BG_SIZE)
    width, height = BG_SIZE
    image.fill((34, 28, 30))
    brick_w, brick_h = 20, 10
    for row in range(height // brick_h + 1):
        offset = (brick_w // 2) * (row % 2)
        for column in range(-1, width // brick_w + 1):
            x0, y0 = column * brick_w + offset, row * brick_h
            tone = rng.randint(-8, 8)
            base = (64 + tone, 57 + tone, 60 + tone)
            for y in range(y0, y0 + brick_h - 1):
                for x in range(x0, x0 + brick_w - 1):
                    if 0 <= x < width and 0 <= y < height:
                        color = base
                        if y == y0 or x == x0:
                            color = shade(base, 1.15)
                        elif y == y0 + brick_h - 2 or x == x0 + brick_w - 2:
                            color = shade(base, 0.82)
                        elif rng.random() < 0.04:
                            color = shade(base, 0.9)
                        image.set_at((x, y), color)
            if rng.random() < 0.12:                            # moss
                for _ in range(6):
                    x, y = x0 + rng.randrange(brick_w - 1), y0 + brick_h - 2 - rng.randrange(3)
                    if 0 <= x < width and 0 <= y < height:
                        image.set_at((x, y), rng.choice([(70, 96, 54), (56, 80, 44)]))

    for torch_x in (34, 286):
        glow(image, (torch_x, 62), 70, (255, 180, 90), 0.7)
        for y in range(66, 82):                                # bracket and torch
            image.set_at((torch_x, y), (60, 44, 34))
            image.set_at((torch_x + 1, y), (60, 44, 34))
        for x in range(torch_x - 2, torch_x + 4):
            image.set_at((x, 80), (90, 90, 96))
        flame = ["..y...", ".yyo..", ".yooy.", "yoorry", ".orrr.", "..rr.."]
        colors = {'y': (255, 236, 140), 'o': (255, 170, 60), 'r': (214, 80, 40)}
        for dy, line in enumerate(flame):
            for dx, key in enumerate(line):
                if key != '.':
                    image.set_at((torch_x - 2 + dx, 58 + dy), colors[key])
    vignette(image, 0.7)
    return image


def tavern_table():
    rng = random.Random(9)
    image = pygame.Surface(BG_SIZE)
    width, height = BG_SIZE
    plank_h = 25
    tones = [(104, 66, 42), (96, 60, 38), (110, 72, 46), (100, 63, 40)]
    for plank in range(height // plank_h + 1):
        base = tones[plank % len(tones)]
        y0 = plank * plank_h
        for y in range(y0, min(y0 + plank_h, height)):
            for x in range(width):
                image.set_at((x, y), base)
        for _ in range(26):                                    # grain streaks
            gx, gy, length = rng.randrange(width), y0 + 2 + rng.randrange(plank_h - 4), rng.randint(10, 50)
            for x in range(gx, min(width, gx + length)):
                if gy < height:
                    image.set_at((x, gy), shade(base, 0.86))
        for _ in range(2):                                     # knots
            kx, ky = rng.randrange(10, width - 10), y0 + rng.randrange(6, plank_h - 6)
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0)):
                if 0 <= ky + dy < height:
                    image.set_at((kx + dx, ky + dy), shade(base, 0.7))
        seam_x = rng.randrange(60, width - 60)                 # where two boards meet
        for y in range(y0, min(y0 + plank_h, height)):
            image.set_at((seam_x, y), shade(base, 0.55))
        for x in range(width):
            if y0 + plank_h - 1 < height:
                image.set_at((x, y0 + plank_h - 1), shade(base, 0.5))
            if y0 < height:
                image.set_at((x, y0), shade(base, 1.12))
        for nail_x in (seam_x - 4, seam_x + 3):
            for nail_y in (y0 + 4, y0 + plank_h - 6):
                if nail_y < height:
                    image.set_at((nail_x, nail_y), (150, 150, 156))
    vignette(image, 0.8)
    return image


BACKGROUNDS = {'sky': night_sky, 'stone': stone_wall, 'table': tavern_table}


def make_backgrounds():
    os.makedirs(BACKGROUND_DIR, exist_ok=True)
    for name, draw in BACKGROUNDS.items():
        image = draw()
        image = pygame.transform.scale(image, (BG_SIZE[0] * BG_SCALE, BG_SIZE[1] * BG_SCALE))
        pygame.image.save(image, os.path.join(BACKGROUND_DIR, f"{name}.png"))


if __name__ == "__main__":
    pygame.init()
    make_portraits()
    make_backgrounds()
    print(f"Portraits written to {PORTRAIT_DIR}, backgrounds to {BACKGROUND_DIR}")
