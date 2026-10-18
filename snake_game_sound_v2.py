"""
NEON SNAKE — Sound Edition
Python 3.11 + Pygame

Place eat.wav, die.wav, and click.wav beside this file. Missing sounds are
skipped independently, so the game remains playable without them.
"""

import json
import math
import os
import random
import sys
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

WIDTH, HEIGHT = 800, 600
CELL = 20
FPS = 60
TITLE = "NEON SNAKE // SOUND EDITION"

BG = (10, 10, 25)
PANEL = (17, 20, 42)
PANEL_ALT = (22, 26, 53)
CYAN = (0, 255, 200)
CYAN_DIM = (0, 120, 115)
MAGENTA = (255, 0, 150)
PURPLE = (100, 100, 255)
WHITE = (245, 250, 255)
MUTED = (145, 157, 185)
GREEN = (100, 255, 145)
GOLD = (255, 211, 90)
RED = (255, 75, 100)

GRID_W, GRID_H = WIDTH // CELL, HEIGHT // CELL
BASE_MOVE_INTERVAL = 135  # milliseconds per grid step
MIN_MOVE_INTERVAL = 65
SCORE_FILE = Path(__file__).resolve().parent / "highscore.json"
SETTINGS_FILE = Path(__file__).resolve().parent / "settings.json"
ASSET_DIR = Path(__file__).resolve().parent

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

FONT_TITLE = pygame.font.SysFont("Segoe UI", 42, bold=True)
FONT_BIG = pygame.font.SysFont("Segoe UI", 30, bold=True)
FONT_MED = pygame.font.SysFont("Segoe UI", 22, bold=True)
FONT_SMALL = pygame.font.SysFont("Segoe UI", 17)
FONT_TINY = pygame.font.SysFont("Segoe UI", 14)

# ---------------------------------------------------------------------------
# Utilities and persistence
# ---------------------------------------------------------------------------
def clamp(value, low, high):
    return max(low, min(high, value))


def draw_text(surface, text, font, color, center=None, topleft=None):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    surface.blit(image, rect)
    return rect


def load_json(path, default):
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else default.copy()
    except (OSError, json.JSONDecodeError, TypeError):
        return default.copy()


def write_json(path, data):
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        # Game play should continue if the folder is read-only.
        pass


def rounded_panel(surface, rect, fill=PANEL, border=CYAN_DIM, radius=12, width=1):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border and width:
        pygame.draw.rect(surface, border, rect, width=width, border_radius=radius)


class SoundManager:
    """Load each sound independently; a missing file won't disable others."""

    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.65
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name in ("eat", "die", "click"):
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(ASSET_DIR / f"{name}.wav"))
                except (pygame.error, OSError):
                    pass
            self.set_volume(self.volume)
        except pygame.error:
            self.enabled = False

    def set_volume(self, volume):
        self.volume = clamp(float(volume), 0.0, 1.0)
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass


# ---------------------------------------------------------------------------
# Buttons and background
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label, action, accent=CYAN):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.accent = accent
        self.hovered = False

    def draw(self, surface):
        fill = (25, 38, 62) if self.hovered else PANEL_ALT
        border = self.accent if self.hovered else CYAN_DIM
        pygame.draw.rect(surface, fill, self.rect, border_radius=9)
        pygame.draw.rect(surface, border, self.rect, 2 if self.hovered else 1, border_radius=9)
        draw_text(surface, self.label, FONT_SMALL, WHITE, center=self.rect.center)

    def update_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.action()
            return True
        return False


def draw_background(surface, offset=0):
    surface.fill(BG)
    # Subtle grid, deliberately low contrast.
    for x in range(0, WIDTH, CELL):
        pygame.draw.line(surface, (17, 22, 43), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, CELL):
        pygame.draw.line(surface, (17, 22, 43), (0, y), (WIDTH, y), 1)
    # Edge accents
    pygame.draw.line(surface, CYAN_DIM, (18, 18), (115, 18), 2)
    pygame.draw.line(surface, MAGENTA, (WIDTH - 115, HEIGHT - 18), (WIDTH - 18, HEIGHT - 18), 2)


def draw_glow(surface, center, radius, color, alpha=35):
    glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color, alpha), (radius * 2, radius * 2), radius * 2)
    pygame.draw.circle(glow, (*color, alpha + 20 if alpha < 235 else 255), (radius * 2, radius * 2), radius)
    surface.blit(glow, (int(center[0] - radius * 2), int(center[1] - radius * 2)))


# ---------------------------------------------------------------------------
# Snake and food
# ---------------------------------------------------------------------------
DIRECTIONS = {
    pygame.K_UP: (0, -1),
    pygame.K_w: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_s: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_a: (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_d: (1, 0),
}


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        cx, cy = GRID_W // 2, GRID_H // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)

    def set_direction(self, direction):
        # Prevent a 180-degree turn into the neck.
        if direction[0] == -self.direction[0] and direction[1] == -self.direction[1]:
            return
        self.next_direction = direction

    def next_head(self):
        dx, dy = self.next_direction
        x, y = self.body[0]
        return x + dx, y + dy

    def move(self, grow=False):
        self.direction = self.next_direction
        head = self.next_head()
        x, y = head
        if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
            return False

        # If not growing, the tail moves away this tick and may be entered.
        collision_body = self.body if grow else self.body[:-1]
        if head in collision_body:
            return False

        self.body.insert(0, head)
        if not grow:
            self.body.pop()
        return True

    def draw(self, surface):
        for index, (gx, gy) in enumerate(reversed(self.body)):
            # Draw tail-to-head so the head remains visually on top.
            real_index = len(self.body) - 1 - index
            rect = pygame.Rect(gx * CELL + 2, gy * CELL + 2, CELL - 4, CELL - 4)
            if real_index == 0:
                draw_glow(surface, rect.center, 9, CYAN, 20)
                pygame.draw.rect(surface, WHITE, rect, border_radius=7)
                # Eyes point toward movement direction.
                dx, dy = self.direction
                if dx:
                    eye_x = rect.centerx + dx * 4
                    eyes = [(eye_x, rect.centery - 4), (eye_x, rect.centery + 4)]
                else:
                    eye_y = rect.centery + dy * 4
                    eyes = [(rect.centerx - 4, eye_y), (rect.centerx + 4, eye_y)]
                for eye in eyes:
                    pygame.draw.circle(surface, BG, eye, 2)
            else:
                pygame.draw.rect(surface, CYAN, rect, border_radius=6)
                inner = rect.inflate(-7, -7)
                if inner.width > 0 and inner.height > 0:
                    pygame.draw.rect(surface, (90, 255, 224), inner, border_radius=3)


class Food:
    def __init__(self, occupied):
        self.position = self.spawn(occupied)
        self.kind = "normal"
        self.created_at = pygame.time.get_ticks()
        self.duration = 9000
        self.choose_kind()

    @staticmethod
    def spawn(occupied):
        available = [(x, y) for x in range(GRID_W) for y in range(GRID_H) if (x, y) not in occupied]
        return random.choice(available) if available else None

    def choose_kind(self):
        # One in five food items is a temporary bonus.
        self.kind = "bonus" if random.random() < 0.20 else "normal"

    @property
    def points(self):
        return 30 if self.kind == "bonus" else 10

    def expired(self, now):
        return self.kind == "bonus" and now - self.created_at > self.duration

    def draw(self, surface, now):
        if self.position is None:
            return
        gx, gy = self.position
        center = (gx * CELL + CELL // 2, gy * CELL + CELL // 2)
        color = GOLD if self.kind == "bonus" else MAGENTA
        pulse = int(2 * (1 + math.sin(now / 150)))
        draw_glow(surface, center, 8 + pulse, color, 22)
        radius = 6 + pulse // 2
        pygame.draw.circle(surface, color, center, radius)
        pygame.draw.circle(surface, WHITE, (center[0] - 2, center[1] - 2), 2)


# ---------------------------------------------------------------------------
# Main game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.sounds = SoundManager()
        self.saved = load_json(SCORE_FILE, {"highscore": 0, "games_played": 0, "food_eaten": 0})
        self.settings = load_json(SETTINGS_FILE, {"difficulty": "Normal", "volume": 0.65, "sound": True})
        self.settings.setdefault("difficulty", "Normal")
        self.settings.setdefault("volume", 0.65)
        self.settings.setdefault("sound", True)
        self.sounds.enabled = bool(self.settings["sound"])
        self.sounds.set_volume(self.settings["volume"])

        self.state = "MENU"
        self.snake = Snake()
        self.food = Food(self.snake.body)
        self.score = 0
        self.food_count = 0
        self.started_at = 0
        self.elapsed = 0
        self.last_move = pygame.time.get_ticks()
        self.new_record = False
        self.notice = ""
        self.notice_until = 0
        self.buttons = []
        self.build_buttons()

    def difficulty_interval(self):
        base = {"Easy": 175, "Normal": 135, "Hard": 105}.get(self.settings["difficulty"], 135)
        # Gradually accelerate every 5 foods, with a hard lower bound.
        return max(MIN_MOVE_INTERVAL, base - (self.food_count // 5) * 8)

    def build_buttons(self):
        self.buttons = []
        if self.state == "MENU":
            self.buttons = [
                Button((290, 300, 220, 44), "PLAY", self.start_game, CYAN),
                Button((290, 354, 220, 44), "SETTINGS", self.open_settings, PURPLE),
                Button((290, 408, 220, 44), "HOW TO PLAY", self.open_help, MAGENTA),
                Button((290, 462, 220, 44), "QUIT", self.quit_game, RED),
            ]
        elif self.state == "GAME_OVER":
            self.buttons = [
                Button((230, 405, 160, 44), "PLAY AGAIN", self.start_game, CYAN),
                Button((410, 405, 160, 44), "MAIN MENU", self.go_menu, MAGENTA),
            ]
        elif self.state == "PAUSED":
            self.buttons = [
                Button((290, 345, 220, 44), "RESUME", self.resume_game, CYAN),
                Button((290, 399, 220, 44), "MAIN MENU", self.go_menu, MAGENTA),
            ]
        elif self.state == "SETTINGS":
            self.buttons = [
                Button((230, 430, 150, 42), "VOLUME -", lambda: self.change_volume(-0.1), PURPLE),
                Button((420, 430, 150, 42), "VOLUME +", lambda: self.change_volume(0.1), PURPLE),
                Button((290, 484, 220, 42), "TOGGLE SOUND", self.toggle_sound, MAGENTA),
                Button((290, 536, 220, 42), "BACK", self.go_menu, CYAN),
            ]
        elif self.state == "HELP":
            self.buttons = [Button((290, 510, 220, 44), "BACK", self.go_menu, CYAN)]

    def set_state(self, state):
        self.state = state
        self.build_buttons()

    def start_game(self):
        self.sounds.play("click")
        self.snake.reset()
        self.score = 0
        self.food_count = 0
        self.food = Food(self.snake.body)
        self.started_at = pygame.time.get_ticks()
        self.elapsed = 0
        self.new_record = False
        self.last_move = pygame.time.get_ticks()
        self.saved["games_played"] = int(self.saved.get("games_played", 0)) + 1
        write_json(SCORE_FILE, self.saved)
        self.set_state("PLAYING")

    def go_menu(self):
        self.sounds.play("click")
        self.set_state("MENU")

    def open_settings(self):
        self.sounds.play("click")
        self.set_state("SETTINGS")

    def open_help(self):
        self.sounds.play("click")
        self.set_state("HELP")

    def quit_game(self):
        self.sounds.play("click")
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def resume_game(self):
        self.sounds.play("click")
        self.last_move = pygame.time.get_ticks()
        self.set_state("PLAYING")

    def change_volume(self, amount):
        self.settings["volume"] = clamp(float(self.settings.get("volume", 0.65)) + amount, 0.0, 1.0)
        self.sounds.set_volume(self.settings["volume"])
        write_json(SETTINGS_FILE, self.settings)
        self.build_buttons()

    def toggle_sound(self):
        self.settings["sound"] = not bool(self.settings.get("sound", True))
        self.sounds.enabled = self.settings["sound"]
        write_json(SETTINGS_FILE, self.settings)
        self.sounds.play("click")
        self.build_buttons()

    def save_run(self):
        old_high = int(self.saved.get("highscore", 0))
        self.new_record = self.score > old_high
        self.saved["highscore"] = max(old_high, self.score)
        self.saved["food_eaten"] = int(self.saved.get("food_eaten", 0)) + self.food_count
        self.saved["last_score"] = self.score
        self.saved["last_survival_seconds"] = self.elapsed // 1000
        write_json(SCORE_FILE, self.saved)

    def game_over(self):
        self.elapsed = max(0, pygame.time.get_ticks() - self.started_at)
        self.sounds.play("die")
        self.save_run()
        self.set_state("GAME_OVER")

    def update(self, now):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update_hover(mouse_pos)

        if self.state != "PLAYING":
            return

        self.elapsed = now - self.started_at
        if now - self.last_move < self.difficulty_interval():
            return
        self.last_move = now

        next_head = self.snake.next_head()
        will_eat = next_head == self.food.position
        if not self.snake.move(grow=will_eat):
            self.game_over()
            return

        if will_eat:
            self.score += self.food.points
            self.food_count += 1
            self.sounds.play("eat")
            self.food = Food(self.snake.body)
            if self.food.position is None:
                self.game_over()
                return
        elif self.food.expired(now):
            self.food = Food(self.snake.body)

    def draw_hud(self):
        rounded_panel(screen, pygame.Rect(18, 16, 190, 58), PANEL, CYAN_DIM)
        draw_text(screen, "SCORE", FONT_TINY, MUTED, topleft=(32, 23))
        draw_text(screen, f"{self.score:04d}", FONT_MED, WHITE, topleft=(32, 39))

        rounded_panel(screen, pygame.Rect(218, 16, 190, 58), PANEL, PURPLE)
        draw_text(screen, "BEST", FONT_TINY, MUTED, topleft=(232, 23))
        draw_text(screen, f"{max(int(self.saved.get('highscore', 0)), self.score):04d}", FONT_MED, WHITE, topleft=(232, 39))

        rounded_panel(screen, pygame.Rect(418, 16, 170, 58), PANEL, MAGENTA)
        draw_text(screen, "FOOD", FONT_TINY, MUTED, topleft=(432, 23))
        draw_text(screen, str(self.food_count), FONT_MED, WHITE, topleft=(432, 39))

        rounded_panel(screen, pygame.Rect(598, 16, 184, 58), PANEL, CYAN_DIM)
        draw_text(screen, "MODE / SPEED", FONT_TINY, MUTED, topleft=(612, 23))
        speed = round(1000 / self.difficulty_interval(), 1)
        draw_text(screen, f"{self.settings['difficulty']}  {speed} t/s", FONT_SMALL, WHITE, topleft=(612, 42))

    def draw_menu(self):
        draw_text(screen, "NEON", FONT_TITLE, CYAN, center=(WIDTH // 2, 115))
        draw_text(screen, "S N A K E", FONT_TITLE, WHITE, center=(WIDTH // 2, 160))
        pygame.draw.line(screen, MAGENTA, (300, 190), (500, 190), 2)
        draw_text(screen, "SOUND EDITION  //  ARCADE PROTOCOL", FONT_TINY, MUTED, center=(WIDTH // 2, 218))
        best = int(self.saved.get("highscore", 0))
        last = int(self.saved.get("last_score", 0))
        draw_text(screen, f"BEST {best:04d}     LAST {last:04d}", FONT_SMALL, GOLD, center=(WIDTH // 2, 260))
        draw_text(screen, "ARROW KEYS / WASD TO MOVE  •  P OR ESC TO PAUSE", FONT_TINY, MUTED, center=(WIDTH // 2, 570))

    def draw_settings(self):
        rounded_panel(screen, pygame.Rect(190, 120, 420, 380), PANEL, CYAN_DIM, 16, 2)
        draw_text(screen, "SETTINGS", FONT_BIG, CYAN, center=(WIDTH // 2, 158))
        draw_text(screen, f"Difficulty: {self.settings['difficulty']}", FONT_MED, WHITE, center=(WIDTH // 2, 220))
        draw_text(screen, "Press 1 = Easy   2 = Normal   3 = Hard", FONT_SMALL, MUTED, center=(WIDTH // 2, 256))
        draw_text(screen, f"Sound: {'ON' if self.settings['sound'] else 'OFF'}", FONT_MED, WHITE, center=(WIDTH // 2, 300))
        draw_text(screen, f"Volume: {round(self.settings['volume'] * 100)}%", FONT_MED, WHITE, center=(WIDTH // 2, 340))
        pygame.draw.rect(screen, (38, 45, 72), (275, 375, 250, 12), border_radius=6)
        pygame.draw.rect(screen, CYAN, (275, 375, int(250 * self.settings["volume"]), 12), border_radius=6)
        draw_text(screen, "Click +/- to adjust volume. Press 1, 2 or 3 to change difficulty.", FONT_TINY, MUTED, center=(WIDTH // 2, 405))

    def draw_help(self):
        rounded_panel(screen, pygame.Rect(160, 110, 480, 370), PANEL, PURPLE, 16, 2)
        draw_text(screen, "HOW TO PLAY", FONT_BIG, CYAN, center=(WIDTH // 2, 150))
        lines = [
            ("ARROWS / WASD", "Move the snake"),
            ("P / ESC", "Pause or resume"),
            ("EAT PINK FOOD", "+10 points"),
            ("EAT GOLD FOOD", "+30 bonus points"),
            ("AVOID WALLS", "and your own body"),
            ("1 / 2 / 3", "Change difficulty in Settings"),
        ]
        y = 200
        for key, description in lines:
            draw_text(screen, key, FONT_SMALL, MAGENTA, topleft=(205, y))
            draw_text(screen, description, FONT_SMALL, WHITE, topleft=(385, y))
            y += 39

    def draw_game_over(self):
        rounded_panel(screen, pygame.Rect(160, 130, 480, 335), PANEL, MAGENTA, 16, 2)
        draw_text(screen, "GAME OVER", FONT_TITLE, MAGENTA, center=(WIDTH // 2, 185))
        draw_text(screen, f"FINAL SCORE  {self.score:04d}", FONT_BIG, WHITE, center=(WIDTH // 2, 245))
        draw_text(screen, f"FOOD EATEN  {self.food_count}", FONT_SMALL, MUTED, center=(WIDTH // 2, 285))
        draw_text(screen, f"SURVIVED  {self.elapsed // 1000}s", FONT_SMALL, MUTED, center=(WIDTH // 2, 315))
        if self.new_record:
            draw_text(screen, "★ NEW PERSONAL BEST ★", FONT_MED, GOLD, center=(WIDTH // 2, 355))
        else:
            draw_text(screen, f"PERSONAL BEST  {self.saved.get('highscore', 0):04d}", FONT_SMALL, GOLD, center=(WIDTH // 2, 355))

    def draw(self, now):
        draw_background(screen)
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "SETTINGS":
            self.draw_settings()
        elif self.state == "HELP":
            self.draw_help()
        elif self.state == "PLAYING":
            self.draw_hud()
            self.snake.draw(screen)
            self.food.draw(screen, now)
            draw_text(screen, "P / ESC  PAUSE", FONT_TINY, MUTED, topleft=(20, HEIGHT - 28))
        elif self.state == "PAUSED":
            self.draw_hud()
            self.snake.draw(screen)
            self.food.draw(screen, now)
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((3, 5, 20, 190))
            screen.blit(shade, (0, 0))
            draw_text(screen, "PAUSED", FONT_TITLE, CYAN, center=(WIDTH // 2, 255))
            draw_text(screen, "Take a breath. The snake is waiting.", FONT_SMALL, MUTED, center=(WIDTH // 2, 300))
        elif self.state == "GAME_OVER":
            self.draw_game_over()

        for button in self.buttons:
            button.draw(screen)

        pygame.display.flip()

    def handle_key(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_p:
            if self.state == "PLAYING":
                self.set_state("PAUSED")
                self.sounds.play("click")
                return
            if self.state == "PAUSED":
                self.resume_game()
                return

        if self.state == "SETTINGS":
            if key in (pygame.K_1, pygame.K_KP1):
                self.settings["difficulty"] = "Easy"
            elif key in (pygame.K_2, pygame.K_KP2):
                self.settings["difficulty"] = "Normal"
            elif key in (pygame.K_3, pygame.K_KP3):
                self.settings["difficulty"] = "Hard"
            else:
                return
            write_json(SETTINGS_FILE, self.settings)
            self.sounds.play("click")
            return

        if self.state == "MENU":
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.start_game()
        elif self.state == "PLAYING":
            if key in DIRECTIONS:
                self.snake.set_direction(DIRECTIONS[key])
        elif self.state == "GAME_OVER":
            if key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self.start_game()
            elif key == pygame.K_m:
                self.go_menu()
            elif key == pygame.K_q:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state in ("SETTINGS", "HELP") and key == pygame.K_BACKSPACE:
            self.go_menu()

    def run(self):
        running = True
        while running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                elif event.type == pygame.MOUSEMOTION:
                    for button in self.buttons:
                        button.update_hover(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = False
                    for button in self.buttons:
                        if button.handle_click(event.pos):
                            self.sounds.play("click")
                            clicked = True
                            break
                    if not clicked and self.state == "PLAYING":
                        pass

            self.update(now)
            self.draw(now)
            clock.tick(FPS)

        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
