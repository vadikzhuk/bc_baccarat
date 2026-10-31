"""Mouse-driven front-end: a quick duel or the roguelike climb.
Run with the project venv, which has pygame: ../venv/bin/python pygame_front.py
Art comes from make_pixel_art.py (portraits, backgrounds); fonts are macOS system fonts with fallbacks.
"""
import os
import random
import pygame
from ai_opponent import choose_attack, choose_defence, choose_loadout
from class_character import CHARACTER_CLASSES
from class_item import MAX_CONSUMABLES
from class_player import Player
from class_run import AFTER_FIGHT_HEAL, FLOORS, Run
from constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, SUIT_SYMBOLS, ZONES
from duel_text import (RULES, ZONE_HINTS, active_lines, ai_prepare, card_name, clash_lines, discard_lines,
                       item_lines, sorted_hand)
from game_backend import Game

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
SYSTEM_FONT_DIR = '/System/Library/Fonts/Supplemental'
TITLE_FONT, BODY_FONT, SYMBOL_FONT = 'Luminari.ttf', 'Silom.ttf', 'Arial.ttf'

CARD_SIZE = (100, 152)
SMALL_CARD_SIZE = (64, 98)
UNIT = 3  # one "pixel" of UI chrome (frames, bevels), to match the chunky art

TEXT = (240, 226, 196)
MUTED = (178, 156, 124)
GOLD = (242, 198, 92)
RED = (214, 76, 64)
GREEN = (118, 190, 88)
HIGHLIGHT = (255, 216, 104)
OUTLINE = (20, 14, 14)

PANEL_STYLE = ((38, 28, 26, 236), (122, 90, 60), (24, 17, 15))       # fill, light bevel, dark bevel
BUTTON_STYLE = ((108, 70, 42, 255), (170, 122, 76), (62, 38, 24))
BUTTON_HOVER_STYLE = ((140, 94, 56, 255), (206, 156, 100), (78, 50, 30))
BUTTON_DISABLED_STYLE = ((70, 64, 62, 255), (104, 98, 94), (44, 40, 40))
SLOT_STYLE = ((22, 16, 14, 200), (24, 17, 15), (96, 72, 50))         # sunken: bevel reversed


# ---------- text ----------

def load_font(file_name, size):
    path = os.path.join(SYSTEM_FONT_DIR, file_name)
    return pygame.font.Font(path if os.path.exists(path) else None, size)


class PixelFont:
    """Renders at a small size without anti-aliasing and scales up with hard edges, so text matches the art.
    The fantasy fonts have no card suits, so those characters come from a fallback font.
    Has the parts of the pygame Font interface the UI uses: render, size, get_linesize.
    """
    SUITS = set(SUIT_SYMBOLS.values())
    RED_SUITS = {SUIT_SYMBOLS['H'], SUIT_SYMBOLS['D']}

    def __init__(self, file_name, size, scale):
        self.font = load_font(file_name, size)
        self.symbols = load_font(SYMBOL_FONT, size + 3)  # suits are tiny at the same size
        self.scale = scale
        self.cache = {}

    def runs(self, text):
        """Splits text into (font, chunk) pieces: plain text, black suits and red suits each get their own chunk."""
        pieces = []
        for char in text:
            kind = 'red' if char in self.RED_SUITS else 'suit' if char in self.SUITS else 'text'
            if pieces and pieces[-1][0] == kind:
                pieces[-1][1] += char
            else:
                pieces.append([kind, char])
        return [(self.font if kind == 'text' else self.symbols, chunk) for kind, chunk in pieces]

    def render(self, text, antialias=False, color=TEXT):
        key = (text, color)
        if key not in self.cache:
            if len(self.cache) > 3000:
                self.cache.clear()
            images = [font.render(chunk, False, self.chunk_color(chunk, color)) for font, chunk in self.runs(text)]
            height = self.font.get_height()
            surface = pygame.Surface((max(1, sum(image.get_width() for image in images)), height), pygame.SRCALPHA)
            x = 0
            for image in images:
                surface.blit(image, (x, (height - image.get_height()) // 2))
                x += image.get_width()
            self.cache[key] = pygame.transform.scale(surface, (surface.get_width() * self.scale, height * self.scale))
        return self.cache[key]

    def chunk_color(self, chunk, color):
        """Hearts and diamonds in red, except in drop shadows."""
        if color != OUTLINE and chunk and all(char in self.RED_SUITS for char in chunk):
            return (226, 72, 60)
        return color

    def size(self, text):
        width = sum(font.size(chunk)[0] for font, chunk in self.runs(text))
        return width * self.scale, self.font.get_height() * self.scale

    def get_linesize(self):
        return self.font.get_linesize() * self.scale


def wrap_text(text, font, width):
    lines = []
    for paragraph in text.split('\n'):
        line = ""
        for word in paragraph.split(' '):
            candidate = f"{line} {word}" if line else word
            if font.size(candidate)[0] <= width:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_text(surface, text, font, color, pos, center=False, shadow=True):
    """Text with a one-unit drop shadow, which keeps it readable on busy pixel backgrounds."""
    image = font.render(text, False, color)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    if shadow:
        surface.blit(font.render(text, False, OUTLINE), rect.move(font.scale, font.scale))
    surface.blit(image, rect)
    return rect


def draw_wrapped(surface, text, font, color, rect):
    """Draws text wrapped to rect's width from its top. Returns the y below the last line."""
    y = rect.top
    for line in wrap_text(text, font, rect.width):
        draw_text(surface, line, font, color, (rect.left, y))
        y += font.get_linesize()
    return y


# ---------- pixel chrome ----------

FRAME_CACHE = {}


def frame_surface(size, style, studs=False):
    """A notched pixel frame: dark outline, bevelled edge, optional gold corner studs."""
    key = (size, style, studs)
    if key not in FRAME_CACHE:
        fill, light, dark = style
        width, height = size
        u = UNIT
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill(OUTLINE, (u, 0, width - 2 * u, height))           # outline with cut corners
        surface.fill(OUTLINE, (0, u, width, height - 2 * u))
        surface.fill(fill, (u, u, width - 2 * u, height - 2 * u))
        surface.fill(light, (u, u, width - 2 * u, u))                   # bevel: light top and left...
        surface.fill(light, (u, u, u, height - 2 * u))
        surface.fill(dark, (u, height - 2 * u, width - 2 * u, u))       # ...dark bottom and right
        surface.fill(dark, (width - 2 * u, u, u, height - 2 * u))
        if studs:
            for x in (2 * u, width - 4 * u):
                for y in (2 * u, height - 4 * u):
                    surface.fill(GOLD, (x, y, 2 * u, 2 * u))
                    surface.fill((150, 110, 40), (x + u, y + u, u, u))
        FRAME_CACHE[key] = surface
    return FRAME_CACHE[key]


def draw_panel(surface, rect, style=PANEL_STYLE, studs=True):
    rect = pygame.Rect(rect)
    surface.blit(frame_surface(rect.size, style, studs), rect)
    return rect


def draw_hp_bar(surface, rect, hp, max_hp, font):
    share = max(min(hp / max_hp, 1), 0)
    surface.fill(OUTLINE, rect)
    inner = rect.inflate(-2 * UNIT, -2 * UNIT)
    surface.fill((70, 30, 30), inner)
    color = GREEN if share > 0.5 else GOLD if share > 0.25 else RED
    fill = pygame.Rect(inner.left, inner.top, int(inner.width * share), inner.height)
    surface.fill(color, fill)
    surface.fill(tuple(min(255, c + 50) for c in color), (fill.left, fill.top, fill.width, UNIT))   # shine
    draw_text(surface, f"{hp} / {max_hp} HP", font, TEXT, rect.center, center=True)


class Images:
    def __init__(self):
        self.cache = {}

    def load(self, name, size, pixelate=False):
        """pixelate: shrink with smoothing, then blow back up with hard edges, so painted art looks pixelated."""
        key = (name, size, pixelate)
        if key not in self.cache:
            image = pygame.image.load(os.path.join(ASSET_DIR, name)).convert_alpha()
            if pixelate:
                small = pygame.transform.smoothscale(image, (size[0] // 2, size[1] // 2))
                image = pygame.transform.scale(small, size)
            else:
                image = pygame.transform.scale(image, size)
            self.cache[key] = image
        return self.cache[key]

    def card(self, card, size=CARD_SIZE):
        rank, suit = card
        return self.load(f"cards/{rank}{suit}.png", size, pixelate=True)

    def card_back(self, size=CARD_SIZE):
        return self.load("cards/blue_back.png", size, pixelate=True)

    def portrait(self, class_name, sex, size):
        """Sizes that are multiples of 40 keep the portrait's pixels square."""
        return self.load(f"portraits/{class_name.lower()}_{sex}.png", (size, size))

    def background(self, name):
        return self.load(f"backgrounds/{name}.png", (SCREEN_WIDTH, SCREEN_HEIGHT))


def draw_portrait(app, player_or_class, sex, rect):
    """Framed portrait. Takes a Player, or a character class plus a sex."""
    rect = pygame.Rect(rect)
    class_name = player_or_class.name if isinstance(player_or_class, type) else player_or_class.character.name
    app.screen.fill(OUTLINE, rect.inflate(2 * UNIT, 2 * UNIT))
    app.screen.blit(app.images.portrait(class_name, sex, rect.width), rect)


class Clickable:
    def __init__(self, rect, on_click, enabled):
        self.rect, self.on_click, self.enabled = rect, on_click, enabled


class App:
    """Immediate-mode UI: each frame the scene draws itself and registers what can be clicked."""

    def __init__(self, screen):
        self.screen = screen
        self.images = Images()
        self.font_small = PixelFont(BODY_FONT, 10, 2)    # Silom below 10px garbles letters like 'e' and 't'
        self.font = PixelFont(BODY_FONT, 11, 2)
        self.font_bold = PixelFont(BODY_FONT, 12, 2)
        self.font_title = PixelFont(TITLE_FONT, 12, 3)
        self.font_huge = PixelFont(TITLE_FONT, 20, 3)
        self.clickables = []
        self.tooltip = None
        self.running = True
        self.scene = MenuScene(self)

    def show(self, scene):
        self.scene = scene

    def mouse_over(self, rect):
        return rect.collidepoint(pygame.mouse.get_pos())

    def clickable(self, rect, on_click, enabled=True, tooltip=None):
        self.clickables.append(Clickable(rect, on_click, enabled))
        if tooltip and self.mouse_over(rect):
            self.tooltip = tooltip

    def button(self, rect, label, on_click, enabled=True, tooltip=None, font=None):
        rect = pygame.Rect(rect)
        hover = enabled and self.mouse_over(rect)
        style = BUTTON_DISABLED_STYLE if not enabled else BUTTON_HOVER_STYLE if hover else BUTTON_STYLE
        draw_panel(self.screen, rect, style, studs=False)
        draw_text(self.screen, label, font or self.font_bold, TEXT if enabled else MUTED, rect.center, center=True)
        self.clickable(rect, on_click, enabled, tooltip)
        return rect

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for clickable in reversed(self.clickables):
                if clickable.enabled and clickable.rect.collidepoint(event.pos):
                    clickable.on_click()
                    return

    def draw(self):
        self.clickables = []
        self.tooltip = None
        self.screen.blit(self.images.background(self.scene.background), (0, 0))
        self.scene.draw()
        if self.tooltip:
            self.draw_tooltip(self.tooltip)
        pygame.display.flip()

    def draw_tooltip(self, text):
        lines = wrap_text(text, self.font_small, 300)
        line_height = self.font_small.get_linesize()
        rect = pygame.Rect(0, 0, 324, len(lines) * line_height + 6 * UNIT)
        x, y = pygame.mouse.get_pos()
        rect.topleft = (min(x + 16, SCREEN_WIDTH - rect.width - 4), max(y - rect.height - 8, 4))
        draw_panel(self.screen, rect, ((16, 12, 12, 246), (90, 70, 50), (10, 8, 8)), studs=False)
        for number, line in enumerate(lines):
            draw_text(self.screen, line, self.font_small, TEXT, (rect.left + 4 * UNIT, rect.top + 3 * UNIT + number * line_height))

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.draw()
            clock.tick(FPS)


# ---------- menus ----------

class MenuScene:
    background = 'sky'

    def __init__(self, app):
        self.app = app

    def draw(self):
        app, screen = self.app, self.app.screen
        draw_text(screen, "Card Duel", app.font_huge, GOLD, (SCREEN_WIDTH // 2, 80), center=True)
        draw_panel(screen, (160, 150, 960, 420))
        y = 180
        for line in RULES.strip().replace("CARD DUEL - you", "You").replace("Brace (0)", "Brace").split('\n'):
            y = draw_wrapped(screen, line.strip(), app.font, TEXT, pygame.Rect(190, y, 900, 400)) + 6
        app.button((330, 610, 290, 60), "Quick Duel", lambda: app.show(ClassSelectScene(app, 'duel')),
                   tooltip="One fight against a random rival. Shop with 10 gold first.", font=app.font_title)
        app.button((660, 610, 290, 60), "The Climb", lambda: app.show(ClassSelectScene(app, 'climb')),
                   tooltip=f"Beat {FLOORS} opponents in a row. HP, items and gold carry over; lose once and it's over.",
                   font=app.font_title)
        app.button((540, 700, 200, 46), "Quit", self.quit)

    def quit(self):
        self.app.running = False


class ClassSelectScene:
    background = 'stone'

    def __init__(self, app, mode):
        self.app, self.mode = app, mode
        self.sexes = {cls: random.choice(('male', 'female')) for cls in CHARACTER_CLASSES}

    def draw(self):
        app, screen = self.app, self.app.screen
        draw_text(screen, "Choose your class", app.font_title, GOLD, (SCREEN_WIDTH // 2, 44), center=True)
        for number, cls in enumerate(CHARACTER_CLASSES):
            rect = pygame.Rect(40 + (number % 3) * 405, 86 + (number // 3) * 316, 390, 300)
            style = BUTTON_HOVER_STYLE if app.mouse_over(rect) else PANEL_STYLE
            draw_panel(screen, rect, style)
            draw_portrait(app, cls, self.sexes[cls], (rect.left + 18, rect.top + 18, 120, 120))
            draw_text(screen, cls.name, app.font_title, GOLD, (rect.left + 156, rect.top + 26))
            draw_text(screen, f"{cls.max_hp} HP", app.font_bold, TEXT, (rect.left + 158, rect.top + 76))
            draw_text(screen, f"{cls.active_name} ({cls.active_timing})", app.font_small, MUTED, (rect.left + 158, rect.top + 106))
            y = draw_wrapped(screen, cls.passive_text, app.font_small, TEXT, pygame.Rect(rect.left + 18, rect.top + 156, 354, 70))
            draw_wrapped(screen, f"{cls.active_name}: {cls.active_text}", app.font_small, MUTED,
                         pygame.Rect(rect.left + 18, y + 8, 354, 70))
            app.clickable(rect, lambda cls=cls: self.choose(cls))
        app.button((40, 736, 160, 46), "Back", lambda: app.show(MenuScene(app)))

    def choose(self, cls):
        app, run = self.app, Run("Hero", cls)
        run.hero.sex = self.sexes[cls]
        if self.mode == 'duel':
            app.show(ShopScene(app, run, "The Merchant", lambda: start_quick_duel(app, run)))
        else:
            app.show(ShopScene(app, run, "Supplies for the climb", lambda: app.show(FloorIntroScene(app, run))))


def start_quick_duel(app, run):
    rival_class = random.choice(CHARACTER_CLASSES)
    rival = Player("Rival", rival_class(), [item() for item in choose_loadout(character_class=rival_class)])

    def on_end(won):
        title = "Victory!" if won else "Defeat"
        app.show(ResultScene(app, title, [f"Final: {run.hero.name} {run.hero.hp} HP, Rival {rival.hp} HP"], run.hero))

    app.show(DuelScene(app, Game(run.hero, rival), on_end))


class ShopScene:
    """Buying a weapon or armor sells the one it replaces. The run object holds gold, stock and inventory."""
    background = 'stone'

    def __init__(self, app, run, title, on_leave):
        self.app, self.run, self.title, self.on_leave = app, run, title, on_leave
        self.message = ""

    def draw(self):
        app, screen, run = self.app, self.app.screen, self.run
        hero = run.hero
        draw_text(screen, self.title, app.font_title, GOLD, (40, 20))
        draw_text(screen, f"{run.gold} gold     {hero.hp}/{hero.max_hp()} HP     one weapon, one armor, up to "
                          f"{MAX_CONSUMABLES} consumables", app.font, TEXT, (42, 66))

        draw_panel(screen, (24, 94, 840, 636))
        for number, item in enumerate(run.shop_stock):
            y = 108 + number * 51
            draw_text(screen, item.name, app.font, TEXT, (48, y))
            draw_text(screen, f"{item.slot}  {item.price}g", app.font_small, MUTED, (48, y + 24))
            draw_wrapped(screen, item.description, app.font_small, TEXT, pygame.Rect(250, y, 466, 50))
            problem = run.buy_problem(item)
            app.button((728, y, 114, 40), f"Buy {item.price}g", lambda item=item: self.buy(item),
                       enabled=problem is None, tooltip=problem and f"Can't buy: {problem}.")

        draw_panel(screen, (880, 96, 376, 630))
        draw_portrait(app, hero, hero.sex, (904, 120, 80, 80))
        draw_text(screen, f"{hero.character.name}", app.font_title, GOLD, (1000, 124))
        draw_text(screen, "Your gear", app.font_bold, TEXT, (1000, 172))
        for number, item in enumerate(run.owned_items()):
            y = 224 + number * 50
            draw_text(screen, item.name, app.font, TEXT, (904, y + 10))
            app.button((1110, y, 124, 40), f"Sell +{run.sell_price(item)}g", lambda item=item: self.sell(item),
                       tooltip=item.description)

        draw_text(screen, self.message, app.font, GOLD, (40, 746))
        app.button((1050, 736, 206, 50), "Continue", self.on_leave, font=app.font_title)

    def buy(self, item):
        replaced = self.run.replaced_by(item)
        self.run.buy(item)
        self.message = f"Bought {item.name}" + (f", sold {replaced.name}." if replaced else ".")

    def sell(self, item):
        self.run.sell(item)
        self.message = f"Sold {item.name}."


def player_panel(app, player, rect):
    """Portrait, name, HP bar, skill status and gear for one player."""
    screen = app.screen
    rect = draw_panel(screen, rect)
    draw_portrait(app, player, player.sex, (rect.left + 15, rect.top + 15, 80, 80))
    left = rect.left + 110
    draw_text(screen, f"{player.name} the {player.character.name}", app.font_small, GOLD, (left, rect.top + 16))
    draw_hp_bar(screen, pygame.Rect(left, rect.top + 42, rect.right - left - 16, 27), player.hp, player.max_hp(), app.font_small)
    draw_text(screen, player.character.status_text(), app.font_small, TEXT, (left, rect.top + 76))
    gear = ', '.join(item.name for item in player.equipment) or 'no gear'
    items = ', '.join(item.name for item in player.consumables) or 'no items'
    draw_wrapped(screen, f"{gear}  |  {items}", app.font_small, MUTED,
                 pygame.Rect(rect.left + 15, rect.top + 106, rect.width - 30, 60))
    app.clickable(rect, lambda: None, tooltip=f"{player.character.passive_text}  {player.character.active_name}: "
                                              f"{player.character.active_text}")


class FloorIntroScene:
    background = 'stone'

    def __init__(self, app, run):
        self.app, self.run = app, run
        self.enemy = run.make_enemy()

    def draw(self):
        app, screen, run, enemy = self.app, self.app.screen, self.run, self.enemy
        title = "The Final Fight" if run.is_final_floor() else f"Floor {run.floor} of {FLOORS}"
        draw_text(screen, title, app.font_huge, GOLD, (SCREEN_WIDTH // 2, 70), center=True)
        for player, x, caption in ((run.hero, 120, "You"), (enemy, 720, f"The {enemy.name}")):
            rect = draw_panel(screen, (x, 140, 440, 520))
            draw_text(screen, caption, app.font_title, GOLD, (rect.centerx, rect.top + 36), center=True)
            draw_portrait(app, player, player.sex, (rect.centerx - 80, rect.top + 70, 160, 160))
            draw_text(screen, player.character.name, app.font_bold, TEXT, (rect.centerx, rect.top + 256), center=True)
            draw_hp_bar(screen, pygame.Rect(rect.left + 40, rect.top + 280, rect.width - 80, 27),
                        player.hp, player.max_hp(), app.font_small)
            y = draw_wrapped(screen, f"Passive: {player.character.passive_text}", app.font_small, TEXT,
                             pygame.Rect(rect.left + 30, rect.top + 326, rect.width - 60, 60))
            y = draw_wrapped(screen, f"{player.character.active_name}: {player.character.active_text}", app.font_small,
                             MUTED, pygame.Rect(rect.left + 30, y + 6, rect.width - 60, 60))
            gear = ', '.join(item.name for item in player.equipment + player.consumables) or 'no gear'
            draw_wrapped(screen, f"Gear: {gear}", app.font_small, TEXT, pygame.Rect(rect.left + 30, y + 10, rect.width - 60, 60))
        draw_text(screen, "VS", app.font_huge, RED, (SCREEN_WIDTH // 2, 380), center=True)
        draw_text(screen, f"{run.gold} gold", app.font_bold, GOLD, (140, 680))
        app.button((540, 700, 200, 60), "Fight!", self.fight, font=app.font_title)

    def fight(self):
        app, run = self.app, self.run
        app.show(DuelScene(app, Game(run.hero, self.enemy), lambda won: after_fight(app, run, self.enemy, won)))


def after_fight(app, run, enemy, won):
    if not won:
        app.show(ResultScene(app, "Your run is over", [f"You fell on floor {run.floor} of {FLOORS} to the {enemy.name}."],
                             run.hero))
    elif run.is_final_floor():
        app.show(ResultScene(app, "The climb is conquered!", [f"You beat the {enemy.name} with {run.hero.hp} HP left."],
                             run.hero))
    else:
        app.show(RewardScene(app, run, run.win_fight()))


class RewardScene:
    background = 'stone'

    def __init__(self, app, run, earned):
        self.app, self.run, self.earned = app, run, earned
        self.options = run.reward_options()

    def draw(self):
        app, screen, run = self.app, self.app.screen, self.run
        draw_text(screen, "Victory!", app.font_huge, GOLD, (SCREEN_WIDTH // 2, 80), center=True)
        draw_panel(screen, (290, 140, 700, 170))
        draw_portrait(app, run.hero, run.hero.sex, (316, 165, 120, 120))
        draw_text(screen, f"+{self.earned} gold", app.font_title, GOLD, (466, 170))
        draw_text(screen, f"Rested: {AFTER_FIGHT_HEAL:.0%} of missing HP back", app.font, TEXT, (466, 216))
        draw_hp_bar(screen, pygame.Rect(466, 254, 300, 27), run.hero.hp, run.hero.max_hp(), app.font_small)
        draw_text(screen, f"{run.gold} gold", app.font_bold, TEXT, (790, 256))
        draw_text(screen, "Choose a reward", app.font_title, TEXT, (SCREEN_WIDTH // 2, 360), center=True)
        for number, (kind, label, apply) in enumerate(self.options):
            app.button((240, 400 + number * 84, 800, 64), label, lambda apply=apply: self.pick(apply), font=app.font)

    def pick(self, apply):
        apply()
        app, run = self.app, self.run
        app.show(ShopScene(app, run, f"The Merchant - next up: floor {run.floor}", lambda: app.show(FloorIntroScene(app, run))))


class ResultScene:
    background = 'sky'

    def __init__(self, app, title, lines, hero):
        self.app, self.title, self.lines, self.hero = app, title, lines, hero

    def draw(self):
        app, screen = self.app, self.app.screen
        draw_panel(screen, (340, 150, 600, 470))
        draw_text(screen, self.title, app.font_huge, GOLD, (SCREEN_WIDTH // 2, 210), center=True)
        draw_portrait(app, self.hero, self.hero.sex, (SCREEN_WIDTH // 2 - 80, 262, 160, 160))
        for number, line in enumerate(self.lines):
            draw_text(screen, line, app.font, TEXT, (SCREEN_WIDTH // 2, 456 + number * 30), center=True)
        app.button((540, 530, 200, 56), "Main menu", lambda: app.show(MenuScene(app)), font=app.font_title)


# ---------- the duel ----------

class DuelScene:
    """Human is player_A, the AI player_B.

    Phases: 'prepare' (attacker uses skills/items, then Ready lets the AI defender react),
    'pick' (choose a card; a defending human may still use skills/items), 'reveal', 'over'.
    """
    background = 'table'

    def __init__(self, app, game, on_end):
        self.app, self.game, self.on_end = app, game, on_end
        self.human, self.ai = game.player_A, game.player_B
        self.log = []
        self.start_turn()

    def add_log(self, lines):
        self.log = (self.log + lines)[-200:]

    def start_turn(self):
        game = self.game
        self.attacker, self.defender = game.get_current_turn()
        self.human_attacking = self.attacker is self.human
        self.selected = None
        self.result = None
        role = "you attack" if self.human_attacking else "you defend"
        if game.is_last_strike():
            role += " (LAST STRIKE)"
        self.add_log(["", f"--- Turn {game.turn_counter}: {role} ---"])
        if not self.human_attacking:
            self.add_log(ai_prepare(game, self.ai, attacking=True))
            self.phase = 'pick'
        elif self.has_options():
            self.phase = 'prepare'
        else:
            self.ready()

    def has_options(self):
        return (self.human.character.can_use_active(self.human, self.human_attacking)
                or self.game.usable_items(self.human, self.human_attacking))

    def can_prepare(self):
        return self.phase == 'prepare' or (self.phase == 'pick' and not self.human_attacking)

    def ready(self):
        """The attacker is done: the AI defender reacts to the announced skills, then cards are picked."""
        self.add_log(ai_prepare(self.game, self.ai, attacking=False))
        self.phase = 'pick'

    def use_active(self):
        info = self.game.use_active(self.human, self.human_attacking)
        self.add_log(active_lines(self.human, info, human_used=True))
        self.forget_missing_selection()

    def use_item(self, item):
        info = self.game.use_item(self.human, item, self.human_attacking)
        self.add_log(item_lines(self.human, item, info, human_used=True))
        self.forget_missing_selection()

    def forget_missing_selection(self):
        """A Smoke Bomb or Blood Pact can change the hand while a card is selected."""
        if self.selected not in self.human.hand:
            self.selected = None

    def select(self, card):
        self.selected = None if self.selected == card else card

    def play(self, card):
        """card=None means brace. The AI picks blind: it never sees the human's card."""
        game, human, ai = self.game, self.human, self.ai
        if self.human_attacking:
            attack_card = card
            defence_card = choose_defence(ai.hand, game.possible_opponent_cards(ai), ai, human)
        else:
            attack_card = choose_attack(ai.hand, game.possible_opponent_cards(ai), ai, human)
            defence_card = card
        self.result = game.play_clash(self.attacker, self.defender, attack_card, defence_card)
        self.add_log(clash_lines(self.result, self.attacker, self.defender))
        self.phase = 'reveal'

    def next_turn(self):
        if self.game.is_game_over():
            winner = self.game.get_winner()
            self.add_log(["", f"{winner} wins!" if winner else "Both fall - it's a draw!"])
            self.phase = 'over'
            return
        self.game.advance_turn()
        self.start_turn()

    # drawing
    def draw(self):
        app, screen, game = self.app, self.app.screen, self.game
        player_panel(app, self.ai, (16, 12, 396, 170))
        self.draw_ai_hand()

        banner = ("You attack" if self.human_attacking else "You defend") + f"  -  turn {game.turn_counter}"
        if game.is_last_strike():
            banner += "  -  last strike!"
        draw_text(screen, banner, app.font_title, GOLD, (620, 214), center=True)

        draw_panel(screen, (16, 196, 290, 210))
        draw_text(screen, "Discard pile", app.font_bold, GOLD, (34, 212))
        draw_text(screen, f"deck: {len(game.deck.deck)}", app.font_small, MUTED, (210, 214))
        for number, line in enumerate(discard_lines(game.discard_pile)):
            draw_wrapped(screen, line, app.font, TEXT, pygame.Rect(34, 248 + number * 38, 256, 40))

        self.draw_clash_area()
        self.draw_log()
        self.draw_actions()
        self.draw_hand()
        player_panel(app, self.human, (16, 582, 318, 206))

    def draw_ai_hand(self):
        app, ai = self.app, self.ai
        revealed = self.human.sees_opponent_hand()
        cards = sorted_hand(ai.hand) if revealed else ai.hand
        for number, card in enumerate(cards):
            image = app.images.card(card, SMALL_CARD_SIZE) if revealed else app.images.card_back(SMALL_CARD_SIZE)
            app.screen.blit(image, (430 + number * 72, 22))
        label = "their hand (marked!)" if revealed else f"their hand: {len(ai.hand)} cards"
        draw_text(app.screen, label, app.font_small, TEXT, (430, 130))

    def draw_clash_area(self):
        app, screen = self.app, self.app.screen
        draw_panel(screen, (322, 240, 562, 252))
        slots = [("Attack", self.result and self.result['attack_card'], 440),
                 ("Defence", self.result and self.result['defence_card'], 664)]
        for (label, card, x), name in zip(slots, (self.attacker.name, self.defender.name)):
            draw_text(screen, f"{label}: {name}", app.font_small, MUTED, (x + 50, 262), center=True)
            rect = pygame.Rect(x, 278, *CARD_SIZE)
            if self.result and card:
                screen.fill(OUTLINE, rect.inflate(2 * UNIT, 2 * UNIT))
                screen.blit(app.images.card(card), rect)
            elif self.result:
                draw_panel(screen, rect, BUTTON_DISABLED_STYLE, studs=False)
                draw_text(screen, "BRACE", app.font_bold, GOLD, rect.center, center=True)
            else:
                draw_panel(screen, rect, SLOT_STYLE, studs=False)
                draw_text(screen, "?", app.font_title, MUTED, rect.center, center=True)

        if self.result:
            outcome = {'parry': "Parry!", 'block': "Blocked", 'crit': "Critical hit!", 'hit': "Struck!"}[self.result['outcome']]
            detail = (f"{self.result['counter_damage']} back to the attacker" if self.result['outcome'] == 'parry'
                      else f"{self.result['damage']} damage")
            draw_text(screen, outcome, app.font_title, HIGHLIGHT, (603, 254 + 196), center=True)
            draw_text(screen, detail, app.font, TEXT, (603, 476), center=True)
        elif self.phase == 'prepare':
            draw_text(screen, "Use a skill or item, then press Ready", app.font, TEXT, (603, 462), center=True)
        else:
            verb = "attack with" if self.human_attacking else "defend with"
            draw_text(screen, f"Pick a card to {verb}", app.font, TEXT, (603, 462), center=True)

    def draw_log(self):
        app, screen = self.app, self.app.screen
        rect = draw_panel(screen, (900, 12, 364, 480))
        lines = []
        for entry in self.log:
            lines += wrap_text(entry, app.font_small, rect.width - 36)
        line_height = app.font_small.get_linesize()
        visible = lines[-((rect.height - 30) // line_height):]
        for number, line in enumerate(visible):
            color = GOLD if line.startswith('---') or line.startswith('>>') else TEXT
            draw_text(screen, line, app.font_small, color, (rect.left + 18, rect.top + 15 + number * line_height))

    def draw_actions(self):
        app, human, game = self.app, self.human, self.game
        x, y = 340, 508
        if self.phase in ('prepare', 'pick'):
            character = human.character
            if character.active_name:
                usable = self.can_prepare() and character.can_use_active(human, self.human_attacking)
                x = app.button((x, y, 176, 46), character.active_name, self.use_active, enabled=usable,
                               tooltip=f"{character.active_text} ({character.status_text()})").right + 10
            usable_items = game.usable_items(human, self.human_attacking) if self.can_prepare() else []
            for item in human.consumables:
                x = app.button((x, y, 156, 46), item.name, lambda item=item: self.use_item(item),
                               enabled=item in usable_items, tooltip=item.description, font=app.font_small).right + 10

        right = 1264
        if self.phase == 'prepare':
            app.button((right - 170, y, 170, 46), "Ready", self.ready)
        elif self.phase == 'pick':
            label = f"Play {card_name(self.selected)}" if self.selected else "Pick a card"
            app.button((right - 170, y, 170, 46), label, lambda: self.play(self.selected), enabled=self.selected is not None)
            if not self.human_attacking and human.can_brace():
                app.button((right - 350, y, 170, 46), "Brace", lambda: self.play(None),
                           tooltip="Play nothing: take the hit, keep your card and draw one extra next refill.")
        elif self.phase == 'reveal':
            label = "See result" if game.is_game_over() else "Next turn"
            app.button((right - 170, y, 170, 46), label, self.next_turn)
        elif self.phase == 'over':
            app.button((right - 170, y, 170, 46), "Continue",
                       lambda: self.on_end(game.get_winner() == self.human.name))

    def draw_hand(self):
        app, screen = self.app, self.app.screen
        picking = self.phase == 'pick'
        for number, card in enumerate(sorted_hand(self.human.hand)):
            rect = pygame.Rect(346 + number * 114, 616, *CARD_SIZE)
            if card == self.selected:
                rect.move_ip(0, -24)
            elif picking and app.mouse_over(rect):
                rect.move_ip(0, -10)
            outline = HIGHLIGHT if card == self.selected else OUTLINE
            screen.fill(outline, rect.inflate(2 * UNIT, 2 * UNIT))
            screen.blit(app.images.card(card), rect)
            app.clickable(rect, lambda card=card: self.select(card), enabled=picking,
                          tooltip=f"{card_name(card)}: {ZONES[card[1]]} - {ZONE_HINTS[card[1]]}")


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Card Duel")
    App(screen).run()
    pygame.quit()


if __name__ == "__main__":
    main()
