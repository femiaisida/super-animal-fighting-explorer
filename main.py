import math
import os
import random
import pygame

from battle import Battle
from creature import Creature


# Simple UI button for menu screens.
class Button:
    def __init__(self, rect, label, font, font_path=None, base_size=24):
        self.rect = rect
        self.label = label
        self.font = font
        self.font_path = font_path
        self.base_size = base_size

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, screen, hovered=False):
        bg = (80, 80, 80) if not hovered else (110, 110, 110)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, (20, 20, 20), self.rect, 2, border_radius=6)
        text = self._fit_text((240, 240, 240))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def _fit_text(self, color):
        text = self.font.render(self.label, True, color)
        if text.get_width() <= self.rect.width - 12:
            return text

        size = self.base_size
        while size > 10:
            size -= 1
            font = pygame.font.Font(self.font_path, size) if self.font_path else pygame.font.Font(None, size)
            text = font.render(self.label, True, color)
            if text.get_width() <= self.rect.width - 12:
                return text
        return text

# Window setup
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Map/grid layout
TILE_SIZE = 64

# Colors
WHITE = (240, 240, 240)
YELLOW = (255, 230, 100)
GREEN = (80, 150, 80)
RED = (150, 60, 60)
ENCOUNTER_COLOR = (200, 150, 40)

# Game states
STATE_INTRO = "INTRO"
STATE_STORY = "STORY"
STATE_SELECTION = "SELECTION"
STATE_MAP = "MAP"
STATE_BATTLE = "BATTLE"
STATE_WIN = "WIN"
STATE_LOSE = "LOSE"

# Stat tuning (balanced player advantage)
PLAYER_STATS = dict(base_hp=100, hp_per_level=25, base_dmg_min=12, base_dmg_max=18, dmg_per_level=2)
ENEMY_STATS = dict(base_hp=90, hp_per_level=22, base_dmg_min=10, base_dmg_max=16, dmg_per_level=2)
BOSS_HP_MULT = 1.25
BOSS_DMG_MULT = 1.15
BOSS_CHANCE = 0.10

# Biomes (assets are validated at load; fallbacks used if missing).
BIOMES = {
    "forest": {
        "bg": "assets/forest.jpg",
        "music": "assets/forest.wav",
        "enemy": ["assets/forest_enemy.png"],
        "boss": ["assets/forest_boss.png"],
        "encounter_tiles": 1,
    },
    "lava": {
        "bg": "assets/lava.jpg",
        "music": "assets/lava.wav",
        "enemy": ["assets/lava_enemy.png"],
        "boss": ["assets/lava_boss.png"],
        "encounter_tiles": 2,
    },
    "ocean": {
        "bg": "assets/ocean.jpg",
        "music": "assets/ocean.wav",
        "enemy": ["assets/ocean_enemy.png"],
        "boss": ["assets/ocean_boss.png"],
        "encounter_tiles": 1,
    },
    "ruins": {
        "bg": "assets/ruins.jpg",
        "music": "assets/ruins.mp3",
        "enemy": ["assets/enemy.png"],
        "boss": ["assets/boss.png"],
        "encounter_tiles": 2,
    },
}


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width, self.screen_height = self.screen.get_size()
        self.is_fullscreen = True
        self.tile_size = max(48, int(64 * (self.screen_width / 1024)))
        pygame.display.set_caption("Super Animal Fighting Explorer")
        self.clock = pygame.time.Clock()
        self.font = self._load_font("assets/PressStart2P.ttf", 24)
        self.title_font = self._load_font("assets/PressStart2P.ttf", 36)
        self.small_font = self._load_font("assets/PressStart2P.ttf", 18)

        self.state = STATE_INTRO
        self.running = True
        self.elapsed = 0.0
        self.story_alpha = 0
        self.story_fade_speed = 220  # alpha per second
        self.story_scroll = 0.0
        self.story_speed = 28.0
        self.story_extra = []
        self.boss_story_pool = [
            "With the boss fallen, a gate flares to life. A new path opens across the Wild.",
            "The air clears and ancient songs return. The gates are waking, one by one.",
            "A distant roar answers your victory. Something greater stirs beyond the ruins.",
        ]
        self.story_lines = self._build_story_lines()

        self.creature_options = ["fire", "water", "nature"]
        self.selection_buttons = []
        self.start_button = None
        self.story_button = None

        self.player = None
        self.enemy = None
        self.battle = None

        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = self.screen_height // self.tile_size

        self.player_pos = (self.grid_width // 2, self.grid_height // 2)
        self.previous_pos = self.player_pos
        self.encounter_tiles = set()
        self.show_debug = False
        self.battles_won = 0
        self.current_biome = None
        self.explored = set()
        self.biome_banner_time = 0.0
        self.show_minimap = True
        self.last_battle_was_boss = False

        self.assets = self._load_assets()
        self.sounds = self._load_sounds()
        self.music_paths = {
            "boss": "assets/boss.wav",
            "victory": "assets/victory.wav",
        }
        self.music_enabled = self.sounds is not None
        self._build_intro_buttons()
        self._build_selection_buttons()
        self._set_biome(random.choice(list(BIOMES.keys())), play_music=False)
        self._spawn_encounter_tiles()

    def _safe_load_image(self, path, size=None, use_alpha=True):
        if not os.path.exists(path):
            print(f"Warning: missing asset '{path}'. Using placeholder.")
            return self._placeholder_surface(size or (128, 128))
        try:
            image = pygame.image.load(path)
            image = image.convert_alpha() if use_alpha else image.convert()
        except pygame.error as exc:
            print(f"Warning: failed to load asset '{path}': {exc}")
            return self._placeholder_surface(size or (128, 128))
        return pygame.transform.smoothscale(image, size) if size else image

    def _load_font(self, path, size):
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except pygame.error as exc:
                print(f"Warning: failed to load font '{path}': {exc}")
        return pygame.font.Font(None, size)

    def _placeholder_surface(self, size):
        surface = pygame.Surface(size)
        surface.fill((70, 70, 70))
        pygame.draw.rect(surface, (200, 60, 60), surface.get_rect(), 3)
        return surface

    def _load_assets(self):
        assets = {}
        assets["selection_bg"] = self._safe_load_image("assets/selection_bg.png", (self.screen_width, self.screen_height), False)
        assets["battle_bg"] = self._safe_load_image("assets/battle_bg.png", (self.screen_width, self.screen_height), False)

        assets["creatures"] = {}
        for element in self.creature_options:
            assets["creatures"][element] = self._safe_load_image(f"assets/{element}.png", (128, 128), True)

        assets["map_creatures"] = {}
        for element in self.creature_options:
            assets["map_creatures"][element] = self._safe_load_image(f"assets/{element}.png", (self.tile_size, self.tile_size), True)

        assets["enemy_sprite"] = self._safe_load_image("assets/enemy.png", (180, 180), True)
        assets["boss_sprite"] = self._safe_load_image("assets/boss.png", (180, 180), True)

        assets["map_enemies"] = {}
        for key, data in BIOMES.items():
            enemy_path = data["enemy"][0] if data.get("enemy") else "assets/enemy.png"
            assets["map_enemies"][key] = self._safe_load_image(enemy_path, (self.tile_size, self.tile_size), True)

        assets["biomes"] = {}
        for key, data in BIOMES.items():
            assets["biomes"][key] = {
                "bg": self._safe_load_image(data["bg"], (self.screen_width, self.screen_height), False),
                "enemy": [
                    self._safe_load_image(path, (180, 180), True) for path in data["enemy"]
                ],
                "boss": [
                    self._safe_load_image(path, (180, 180), True) for path in data["boss"]
                ],
            }

        return assets

    def _load_sounds(self):
        sounds = {"attack": None, "click": None}
        try:
            pygame.mixer.init()
        except pygame.error as exc:
            print(f"Warning: audio disabled: {exc}")
            return None

        sounds["attack"] = self._safe_load_sound("assets/attack.wav")
        sounds["click"] = self._safe_load_sound("assets/button-click-.wav")
        return sounds

    def _safe_load_sound(self, path):
        if not os.path.exists(path):
            print(f"Warning: missing sound '{path}'.")
            return None
        try:
            return pygame.mixer.Sound(path)
        except pygame.error as exc:
            print(f"Warning: failed to load sound '{path}': {exc}")
            return None

    def _build_selection_buttons(self):
        self.selection_buttons.clear()
        btn_w = 200
        btn_h = 200
        spacing = 100
        total_w = btn_w * len(self.creature_options) + spacing * (len(self.creature_options) - 1)
        start_x = (self.screen_width - total_w) // 2
        y = int(self.screen_height * 0.35)
        for i, element in enumerate(self.creature_options):
            rect = pygame.Rect(start_x + i * (btn_w + spacing), y, btn_w, btn_h)
            self.selection_buttons.append((element, rect))

    def _build_intro_buttons(self):
        self.start_button = Button(
            pygame.Rect((self.screen_width - 200) // 2, int(self.screen_height * 0.68), 200, 50),
            "START GAME",
            self.font,
            font_path="assets/PressStart2P.ttf",
            base_size=24,
        )
        self.story_button = Button(
            pygame.Rect((self.screen_width - 320) // 2, int(self.screen_height * 0.80), 320, 50),
            "CHOOSE CREATURE",
            self.font,
            font_path="assets/PressStart2P.ttf",
            base_size=24,
        )

    def _set_biome(self, biome_key, play_music=True):
        if biome_key not in BIOMES:
            biome_key = "forest"
        self.current_biome = biome_key
        self.explored = {self.player_pos}
        self.biome_banner_time = 2.5
        if play_music:
            self._play_music("biome", loop=-1)

    def _spawn_encounter_tiles(self):
        self.encounter_tiles.clear()
        count = BIOMES[self.current_biome].get("encounter_tiles", 1)
        while len(self.encounter_tiles) < count:
            tile = (random.randint(0, self.grid_width - 1), random.randint(0, self.grid_height - 1))
            if tile != self.player_pos:
                self.encounter_tiles.add(tile)

    def _create_creature(self, element):
        creature = Creature(element, level=1)
        creature.sprite = self.assets["creatures"][element]
        return creature

    def _configure_for_battle(self, player, enemy):
        player.configure_stats(**PLAYER_STATS)
        player.reset_after_battle()
        enemies = enemy if isinstance(enemy, list) else [enemy]
        for foe in enemies:
            foe.configure_stats(**ENEMY_STATS)
            foe.reset_after_battle()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.elapsed += dt
            self._handle_events()
            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
                self.show_debug = not self.show_debug
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                self.show_minimap = not self.show_minimap
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self._toggle_fullscreen()
                continue

            if self.state == STATE_SELECTION:
                self._handle_selection_event(event)
            elif self.state == STATE_INTRO:
                self._handle_intro_event(event)
            elif self.state == STATE_STORY:
                self._handle_story_event(event)
            elif self.state == STATE_MAP:
                self._handle_map_event(event)
            elif self.state == STATE_BATTLE:
                self.battle.handle_event(event)
            elif self.state == STATE_WIN:
                self._handle_win_event(event)
            elif self.state == STATE_LOSE:
                self._handle_lose_event(event)

    def _handle_selection_event(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        for element, rect in self.selection_buttons:
            if rect.collidepoint(event.pos):
                self._play_sound("click")
                self._stop_music()
                self.player = self._create_creature(element)
                self.player_pos = (self.grid_width // 2, self.grid_height // 2)
                self._set_biome(random.choice(list(BIOMES.keys())), play_music=True)
                self._spawn_encounter_tiles()
                self.state = STATE_MAP
                return

    def _handle_intro_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._play_sound("click")
            self.state = STATE_STORY
            self.story_alpha = 0
            self.story_scroll = 0.0
            return
        if self.start_button and self.start_button.is_clicked(event):
            self._play_sound("click")
            self.state = STATE_STORY
            self.story_alpha = 0
            self.story_scroll = 0.0

    def _handle_story_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._play_sound("click")
            self.state = STATE_SELECTION
            return
        if self.story_button and self.story_button.is_clicked(event):
            self._play_sound("click")
            self.state = STATE_SELECTION

    def _handle_map_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        dx, dy = 0, 0
        if event.key == pygame.K_LEFT:
            dx = -1
        elif event.key == pygame.K_RIGHT:
            dx = 1
        elif event.key == pygame.K_UP:
            dy = -1
        elif event.key == pygame.K_DOWN:
            dy = 1

        if dx == 0 and dy == 0:
            return

        # Move player on grid; battle triggers only on stepping onto encounter tile.
        new_x = max(0, min(self.player_pos[0] + dx, self.grid_width - 1))
        new_y = max(0, min(self.player_pos[1] + dy, self.grid_height - 1))
        self.previous_pos = self.player_pos
        self.player_pos = (new_x, new_y)
        self.explored.add(self.player_pos)

        if self.player_pos in self.encounter_tiles:
            self._start_battle()

    def _handle_win_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.state = STATE_MAP
            self.player.reset_after_battle()
            self.player_pos = self.previous_pos
            self._stop_music()
            self._set_biome(random.choice(list(BIOMES.keys())), play_music=True)
            self._spawn_encounter_tiles()

    def _handle_lose_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if event.key == pygame.K_RETURN:
            self.state = STATE_SELECTION
            self.player = None
            self.enemy = None
            self.battle = None
            self.battles_won = 0
            self._stop_music()
        elif event.key == pygame.K_r and self.player:
            # Quick restart with the same creature.
            element = self.player.element
            self.player = self._create_creature(element)
            self.player_pos = (self.grid_width // 2, self.grid_height // 2)
            self._set_biome(random.choice(list(BIOMES.keys())), play_music=True)
            self._spawn_encounter_tiles()
            self.battles_won = 0
            self.state = STATE_MAP

    def _start_battle(self):
        is_boss = random.random() < BOSS_CHANCE
        biome_assets = self.assets["biomes"][self.current_biome]
        if is_boss:
            self.enemy = Creature("boss", level=self.player.level)
            self.enemy.sprite = random.choice(biome_assets["boss"])
            enemies = self.enemy
        else:
            enemy_count = random.randint(1, 3)
            enemies = []
            for _ in range(enemy_count):
                foe = Creature("enemy", level=self.player.level)
                foe.sprite = random.choice(biome_assets["enemy"])
                enemies.append(foe)
            self.enemy = enemies
        self._configure_for_battle(self.player, enemies)
        if is_boss:
            self.enemy.max_health = int(self.enemy.max_health * BOSS_HP_MULT)
            self.enemy.current_health = self.enemy.max_health
            self.enemy.damage_min = int(self.enemy.damage_min * BOSS_DMG_MULT)
            self.enemy.damage_max = int(self.enemy.damage_max * BOSS_DMG_MULT)
            self._play_music("boss", loop=-1)
        else:
            self._stop_music()
        self.battle = Battle(
            self.player,
            enemies,
            self.font,
            attack_sound=self.sounds.get("attack") if self.sounds else None,
            click_sound=self.sounds.get("click") if self.sounds else None,
            small_font=self.small_font,
            screen_size=(self.screen_width, self.screen_height),
        )
        self.last_battle_was_boss = is_boss
        self.state = STATE_BATTLE

    def _update(self, dt):
        if self.biome_banner_time > 0:
            self.biome_banner_time = max(0.0, self.biome_banner_time - dt)

        if self.state == STATE_STORY:
            self.story_alpha = min(255, self.story_alpha + int(self.story_fade_speed * dt))
            self.story_scroll += self.story_speed * dt

        if self.state == STATE_BATTLE and self.battle:
            self.battle.update(dt)
            if self.battle.outcome == "WIN":
                self.player.level_up()
                self.player.configure_stats(**PLAYER_STATS)
                self.player.reset_after_battle()
                self.battles_won += 1
                if self.last_battle_was_boss:
                    self._extend_story_after_boss()
                self.state = STATE_WIN
                self._play_music("victory", loop=0)
            elif self.battle.outcome == "LOSE":
                self.state = STATE_LOSE
                self._stop_music()

    def _draw(self):
        if self.state == STATE_SELECTION:
            self._draw_selection()
        elif self.state == STATE_INTRO:
            self._draw_intro()
        elif self.state == STATE_STORY:
            self._draw_story()
        elif self.state == STATE_MAP:
            self._draw_map()
        elif self.state == STATE_BATTLE:
            self._draw_battle()
        elif self.state == STATE_WIN:
            self._draw_win()
        elif self.state == STATE_LOSE:
            self._draw_lose()

        pygame.display.flip()

    def _draw_intro(self):
        self.screen.blit(self.assets["selection_bg"], (0, 0))
        title = "SUPER ANIMAL"
        subtitle = "FIGHTING EXPLORER"
        bob = int(6 * math.sin(self.elapsed * 2.0))
        pulse = 32 + int(2 * math.sin(self.elapsed * 3.0))
        title_font = self._load_font("assets/PressStart2P.ttf", pulse)
        self._draw_text_centered(title, self.screen_width // 2, 150 + bob, YELLOW, font=title_font)
        self._draw_text_centered(subtitle, self.screen_width // 2, 220 + bob, YELLOW, font=self.title_font)
        self._draw_text_centered("Press Enter to start", self.screen_width // 2, 320, WHITE, font=self.small_font)
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)
        if self.start_button:
            mouse_pos = pygame.mouse.get_pos()
            self.start_button.draw(self.screen, hovered=self.start_button.is_hovered(mouse_pos))
        self._draw_debug_overlay()

    def _draw_story(self):
        self.screen.fill((0, 0, 0))
        self._draw_text_centered("A LONG TIME AGO...", self.screen_width // 2, 80, YELLOW, font=self.small_font)

        base_y = self.screen_height + 60
        line_height = 36
        for i, line in enumerate(self.story_lines):
            y = base_y - self.story_scroll + i * line_height
            if y < -100:
                continue
            if y > self.screen_height + 100:
                continue

            depth = (self.screen_height - y) / self.screen_height
            scale = max(0.4, 1.1 - depth * 0.9)
            font = self._load_font("assets/PressStart2P.ttf", int(26 * scale))
            text_surface = font.render(line, True, (255, 230, 100))
            if self.story_alpha < 255:
                text_surface.set_alpha(self.story_alpha)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, int(y)))
            self.screen.blit(text_surface, text_rect)

        self._draw_text_centered(
            "Press Enter to choose your creature",
            self.screen_width // 2,
            self.screen_height - 70,
            WHITE,
            font=self.small_font,
            alpha=self.story_alpha,
        )
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)
        if self.story_button:
            mouse_pos = pygame.mouse.get_pos()
            self.story_button.draw(self.screen, hovered=self.story_button.is_hovered(mouse_pos))
        self._draw_debug_overlay()

    def _draw_selection(self):
        self.screen.blit(self.assets["selection_bg"], (0, 0))
        self._draw_text_centered("Select Your Creature", self.screen_width // 2, 120, YELLOW, font=self.title_font)
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)

        mouse_pos = pygame.mouse.get_pos()
        for element, rect in self.selection_buttons:
            hovered = rect.collidepoint(mouse_pos)
            color = (160, 160, 160) if hovered else (60, 60, 60)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, (20, 20, 20), rect, 2, border_radius=8)

            sprite = self.assets["creatures"][element]
            self.screen.blit(sprite, (rect.x + 36, rect.y + 36))
            self._draw_text_centered(element.capitalize(), rect.centerx, rect.y + 170, WHITE, font=self.small_font)
        self._draw_debug_overlay()

    def _draw_map(self):
        self.screen.blit(self.assets["biomes"][self.current_biome]["bg"], (0, 0))

        # Draw encounter tile as a subtle marker.
        for tile_x, tile_y in self.encounter_tiles:
            px = tile_x * self.tile_size
            py = tile_y * self.tile_size
            enemy_sprite = self.assets["map_enemies"].get(self.current_biome)
            if enemy_sprite:
                self.screen.blit(enemy_sprite, (px, py))
            else:
                encounter_rect = pygame.Rect(px, py, self.tile_size, self.tile_size)
                pygame.draw.rect(self.screen, ENCOUNTER_COLOR, encounter_rect, 2)

        if self.player:
            sprite = self.assets["map_creatures"][self.player.element]
            px = self.player_pos[0] * self.tile_size
            py = self.player_pos[1] * self.tile_size
            self.screen.blit(sprite, (px, py))

        self._draw_text(f"Biome: {self.current_biome.capitalize()}", 20, 20, WHITE, font=self.small_font)
        self._draw_text("Explore with arrow keys", 20, 48, WHITE, font=self.small_font)
        self._draw_text("Press F3 for debug overlay", 20, 76, WHITE, font=self.small_font)
        self._draw_text("Press F4 to toggle minimap", 20, 104, WHITE, font=self.small_font)
        self._draw_text("Press F11 to toggle fullscreen", 20, 132, WHITE, font=self.small_font)
        if self.show_minimap:
            self._draw_minimap()
        if self.biome_banner_time > 0:
            self._draw_text_centered(
                f"Entering {self.current_biome.capitalize()}",
                self.screen_width // 2,
                110,
                YELLOW,
                font=self.title_font,
            )
        self._draw_debug_overlay()

    def _draw_battle(self):
        self.screen.blit(self.assets["battle_bg"], (0, 0))
        if self.battle:
            self.battle.draw(self.screen)
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)
        self._draw_debug_overlay()

    def _draw_win(self):
        self.screen.fill(GREEN)
        self._draw_text_centered("Victory!", self.screen_width // 2, 220, YELLOW, font=self.title_font)
        self._draw_text_centered(
            "You healed before returning to the map",
            self.screen_width // 2,
            300,
            WHITE,
            font=self.small_font,
        )
        self._draw_text_centered("Level Up!", self.screen_width // 2, 360, WHITE, font=self.font)
        if self.last_battle_was_boss:
            self._draw_text_centered(
                "New story chapter unlocked",
                self.screen_width // 2,
                400,
                WHITE,
                font=self.small_font,
            )
        self._draw_text_centered("Press Enter to continue", self.screen_width // 2, 440, WHITE, font=self.small_font)
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)
        self._draw_debug_overlay()

    def _draw_lose(self):
        self.screen.fill(RED)
        self._draw_text_centered("Defeat!", self.screen_width // 2, 220, YELLOW, font=self.title_font)
        self._draw_text_centered(
            "Press Enter to return to selection",
            self.screen_width // 2,
            340,
            WHITE,
            font=self.small_font,
        )
        self._draw_text_centered("Press R to restart quickly", self.screen_width // 2, 390, WHITE, font=self.small_font)
        self._draw_text("Press F3 for debug overlay", 20, 20, WHITE, font=self.small_font)
        self._draw_debug_overlay()

    def _draw_text(self, text, x, y, color, font=None, alpha=255):
        draw_font = font or self.font
        surface = draw_font.render(text, True, color)
        if alpha < 255:
            surface.set_alpha(alpha)
        self.screen.blit(surface, (x, y))

    def _draw_text_centered(self, text, center_x, y, color, font=None, alpha=255):
        draw_font = font or self.font
        surface = draw_font.render(text, True, color)
        if alpha < 255:
            surface.set_alpha(alpha)
        rect = surface.get_rect(center=(center_x, y))
        self.screen.blit(surface, rect)

    def _draw_minimap(self):
        map_width = 200
        map_height = 200
        pad = 16
        mini = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        mini.fill((10, 10, 10, 180))

        tile_w = map_width / self.grid_width
        tile_h = map_height / self.grid_height

        for (x, y) in self.explored:
            rect = pygame.Rect(int(x * tile_w), int(y * tile_h), max(1, int(tile_w)), max(1, int(tile_h)))
            pygame.draw.rect(mini, (80, 80, 80, 200), rect)

        for (x, y) in self.encounter_tiles:
            rect = pygame.Rect(int(x * tile_w), int(y * tile_h), max(1, int(tile_w)), max(1, int(tile_h)))
            pygame.draw.rect(mini, (200, 150, 40, 220), rect)

        px, py = self.player_pos
        player_rect = pygame.Rect(int(px * tile_w), int(py * tile_h), max(2, int(tile_w)), max(2, int(tile_h)))
        pygame.draw.rect(mini, (80, 200, 80, 255), player_rect)

        self.screen.blit(mini, (self.screen_width - map_width - pad, pad))

    def _draw_wrapped_text(self, text, x, y, max_width, color, font=None, line_height=28, alpha=255):
        draw_font = font or self.font
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if draw_font.size(test_line)[0] <= max_width:
                line = test_line
            else:
                self._draw_text(line, x, y, color, font=draw_font, alpha=alpha)
                y += line_height
                line = word
        if line:
            self._draw_text(line, x, y, color, font=draw_font, alpha=alpha)

    def _build_story_lines(self):
        segments = [
            (
            "Long ago, the Wild fractured into elemental zones. Ancient gates fell "
            "silent, and the land began to fade. You are an explorer chosen to "
            "bond with a creature and reignite the gates. Each victory restores "
            "balance—each loss lets the Wild slip further away."
            )
        ]
        segments.extend(self.story_extra)
        max_width = min(780, self.screen_width - 200)
        lines = []
        for idx, segment in enumerate(segments):
            if idx > 0:
                lines.append("")
            lines.extend(self._wrap_text_lines(segment, max_width, self.font))
        return lines

    def _extend_story_after_boss(self):
        if self.boss_story_pool:
            next_segment = self.boss_story_pool.pop(0)
        else:
            next_segment = "Another gate awakens. The Wild remembers your name."
        self.story_extra.append(next_segment)
        self.story_lines = self._build_story_lines()

    def _wrap_text_lines(self, text, max_width, font):
        words = text.split()
        lines = []
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
        return lines

    def _draw_debug_overlay(self):
        if not self.show_debug:
            return

        fps = int(self.clock.get_fps())
        level = self.player.level if self.player else "-"
        biome = self.current_biome if self.current_biome else "-"
        encounter = len(self.encounter_tiles)
        player_pos = self.player_pos if self.player_pos else "-"
        lines = [
            f"FPS: {fps}",
            f"Level: {level}",
            f"Battles Won: {self.battles_won}",
            f"Biome: {biome}",
            f"Encounter Tiles: {encounter}",
            f"Player: {player_pos}",
        ]
        x, y = 20, self.screen_height - 110
        for line in lines:
            self._draw_text(line, x, y, WHITE, font=self.small_font)
            y += 22

    def _toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.screen_width, self.screen_height = self.screen.get_size()
        self.tile_size = max(48, int(64 * (self.screen_width / 1024)))
        self.grid_width = self.screen_width // self.tile_size
        self.grid_height = self.screen_height // self.tile_size

        self.assets = self._load_assets()
        self._build_intro_buttons()
        self._build_selection_buttons()
        self._spawn_encounter_tiles()
        self.story_lines = self._build_story_lines()

    def _play_sound(self, key):
        sound = self.sounds.get(key) if self.sounds else None
        if sound:
            sound.play()

    def _play_music(self, key, loop=-1):
        if not self.music_enabled:
            return
        path = self.music_paths.get(key)
        if key == "biome" and self.current_biome:
            path = BIOMES[self.current_biome]["music"]
        if not path or not os.path.exists(path):
            print(f"Warning: missing music '{path}'.")
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=loop)
        except pygame.error as exc:
            print(f"Warning: failed to play music '{path}': {exc}")

    def _stop_music(self):
        if self.music_enabled:
            pygame.mixer.music.stop()


if __name__ == "__main__":
    Game().run()
