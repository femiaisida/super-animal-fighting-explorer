import pygame
import os

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")


def asset_path(filename):
    return os.path.join(ASSETS_DIR, filename)


def _detect_audio_format(path):
    """Read file magic bytes to detect actual audio format."""
    try:
        with open(path, "rb") as f:
            header = f.read(12)
        if header[:3] == b"ID3" or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
            return "mp3"
        if header[:4] == b"OggS":
            return "ogg"
        if header[:4] == b"RIFF":
            return "wav"
        if header[4:8] == b"ftyp" or header[:4] in (b"\x00\x00\x00\x18", b"\x00\x00\x00\x1c"):
            return "m4a"
        if header[:3] == b"fLa":
            return "flac"
    except Exception:
        pass
    return "unknown"


def _music_format_attempts(path):
    """Return list of paths to try, handling mislabelled extensions."""
    import os, shutil
    ext    = os.path.splitext(path)[1].lower()
    actual = _detect_audio_format(path)
    attempts = [path]
    # If extension doesn't match content, make a copy with correct extension
    if actual != "unknown" and f".{actual}" != ext:
        correct = os.path.splitext(path)[0] + f".{actual}"
        if not os.path.exists(correct):
            try:
                shutil.copy2(path, correct)
            except Exception:
                correct = None
        if correct:
            attempts.insert(0, correct)   # try correct extension first
    return attempts, actual


class AssetManager:
    def __init__(self, screen_w=800, screen_h=600):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.images   = {}
        self.sounds   = {}
        self.fonts    = {}
        self._music_files = {}

    def load_image(self, name, filename, scale=None):
        path = asset_path(filename)
        try:
            raw = pygame.image.load(path)
            # Try convert_alpha first (for PNGs with transparency)
            # Fall back to convert() for images without alpha channel
            try:
                img = raw.convert_alpha()
            except Exception:
                img = raw.convert()
            if scale:
                img = pygame.transform.scale(img, scale)
            self.images[name] = img
            print(f"[Assets] ✓  {filename}")
        except Exception as e:
            print(f"[Assets] -  MISSING {filename}")
            self.images[name] = None

    def get_image(self, name):
        if name is None:
            return None
        img = self.images.get(name)
        # Evolved sprite fallback to base
        if img is None and isinstance(name, str) and name.endswith("_evolved"):
            base = name.replace("_evolved", "")
            return self.images.get(base)
        return img

    def load_sound(self, name, filename):
        path = asset_path(filename)
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
            print(f"[Assets] ✓  {filename}")
        except Exception as e:
            print(f"[Assets] -  MISSING sound {filename}")
            self.sounds[name] = None

    def get_sound(self, name):
        return self.sounds.get(name)

    def play_sound(self, name):
        s = self.get_sound(name)
        if s:
            s.play()

    def load_font(self, name, filename, size):
        path = asset_path(filename)
        try:
            self.fonts[name] = pygame.font.Font(path, size)
            print(f"[Assets] ✓  {filename} @ {size}px")
        except Exception as e:
            print(f"[Assets] -  MISSING font {filename}, using fallback")
            self.fonts[name] = pygame.font.SysFont("Arial", size)

    def get_font(self, name):
        return self.fonts.get(name)

    def render_fitted(self, font_name, text, colour, max_w):
        """Render text scaled down to fit max_w pixels wide."""
        font = self.get_font(font_name)
        if not font:
            return None
        surf = font.render(text, True, colour)
        if surf.get_width() > max_w and max_w > 0:
            scale = max_w / surf.get_width()
            new_w = int(surf.get_width() * scale)
            new_h = int(surf.get_height() * scale)
            surf = pygame.transform.scale(surf, (new_w, new_h))
        return surf

    def register_music(self, name, stem):
        """Register a music track by stem name (no extension).
        Stores the stem; play_music resolves the actual file at play time."""
        self._music_files[name] = stem   # stem = base filename without extension

    def play_music(self, name, loops=-1):
        import os
        # Don't restart if already playing the same track
        if getattr(self, "_current_music", None) == name:
            return  # already playing this track
        stem = self._music_files.get(name)
        if not stem:
            return
        # Scan the actual assets directory for a file matching the stem
        # This handles any extension the user has (.mp3, .ogg, .wav, .flac, etc.)
        stem_base = stem.rsplit(".", 1)[0].lower()
        found_path = None
        try:
            for fname in os.listdir(ASSETS_DIR):
                fbase, fext = os.path.splitext(fname)
                if fbase.lower() == stem_base and fext.lower() in (".ogg", ".mp3", ".wav", ".flac"):
                    found_path = os.path.join(ASSETS_DIR, fname)
                    break
        except Exception:
            pass
        if found_path:
            attempts, actual_fmt = _music_format_attempts(found_path)
            loaded = False
            for attempt_path in attempts:
                try:
                    pygame.mixer.music.load(attempt_path)
                    pygame.mixer.music.play(loops)
                    self._current_music = name
                    loaded = True
                    break
                except Exception:
                    continue
            if loaded:
                return
            if not getattr(self, "_music_missing_warned", None):
                self._music_missing_warned = set()
            if name not in self._music_missing_warned:
                if actual_fmt in ("m4a", "unknown"):
                    print(f"[Assets] Music '{name}': file is {actual_fmt.upper()} format — "
                          f"pygame cannot play this. Convert to MP3 or OGG using Audacity or ffmpeg.")
                else:
                    print(f"[Assets] Music '{name}': could not load ({actual_fmt} file)")
                self._music_missing_warned.add(name)
            return
        # Only warn once per missing track
        if not getattr(self, "_music_missing_warned", None):
            self._music_missing_warned = set()
        if name not in self._music_missing_warned:
            print(f"[Assets] Music '{name}': no file matching '{stem_base}.*' in assets/")
            self._music_missing_warned.add(name)

    def stop_music(self):
        self._current_music = None
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.unload()
        except Exception:
            pass

    def load_all(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception:
            pass

        # ── Fonts ──────────────────────────────────────────────────────────────
        _fs = max(8, int(self.screen_h / 54))
        self.load_font("small",  "PressStart2P.ttf", _fs)
        self.load_font("medium", "PressStart2P.ttf", int(_fs * 1.4))
        self.load_font("large",  "PressStart2P.ttf", int(_fs * 2.0))

        sw, sh = self.screen_w, self.screen_h

        # ── Backgrounds ────────────────────────────────────────────────────────
        self.load_image("battle_bg",    "battle_bg.png",    scale=(sw, sh))
        self.load_image("map_bg",       "map_bg.png",       scale=(sw, sh))
        self.load_image("selection_bg", "selection_bg.png", scale=(sw, sh))
        self.load_image("bg_forest",    "forest.jpg",       scale=(sw, sh))
        self.load_image("bg_lava",      "lava.jpg",         scale=(sw, sh))
        self.load_image("bg_ocean",     "ocean.jpg",        scale=(sw, sh))
        self.load_image("bg_ruins",     "ruins.jpg",        scale=(sw, sh))

        # ── Player characters (base) ───────────────────────────────────────────
        self.load_image("fire",   "fire.png",   scale=(128, 128))
        self.load_image("water",  "water.png",  scale=(128, 128))
        self.load_image("nature", "nature.png", scale=(128, 128))
        self.load_image("void",   "void.png",   scale=(128, 128))

        # ── Player characters (evolved stages 1–3) ───────────────────────────
        # Stage 1 (keep old _evolved filenames as evo1 for backwards compat)
        self.load_image("fire_evo1",   "fire_evo1.png",   scale=(128, 128))
        self.load_image("water_evo1",  "water_evo1.png",  scale=(128, 128))
        self.load_image("nature_evo1", "nature_evo1.png", scale=(128, 128))
        self.load_image("void_evo1",   "void_evo1.png",   scale=(128, 128))
        # Stage 2
        self.load_image("fire_evo2",   "fire_evo2.png",   scale=(128, 128))
        self.load_image("water_evo2",  "water_evo2.png",  scale=(128, 128))
        self.load_image("nature_evo2", "nature_evo2.png", scale=(128, 128))
        self.load_image("void_evo2",   "void_evo2.png",   scale=(128, 128))
        # Stage 3
        self.load_image("fire_evo3",   "fire_evo3.png",   scale=(128, 128))
        self.load_image("water_evo3",  "water_evo3.png",  scale=(128, 128))
        self.load_image("nature_evo3", "nature_evo3.png", scale=(128, 128))
        self.load_image("void_evo3",   "void_evo3.png",   scale=(128, 128))

        # ── Normal enemies (tier 1 — base) ────────────────────────────────────
        self.load_image("enemy",         "enemy.png",         scale=(128, 128))
        self.load_image("forest_enemy",  "forest_enemy.png",  scale=(128, 128))
        self.load_image("lava_enemy",    "lava_enemy.png",    scale=(128, 128))
        self.load_image("ocean_enemy",   "ocean_enemy.png",   scale=(128, 128))
        # ── Tier 2 enemies ─────────────────────────────────────────────────────
        self.load_image("forest_enemy2", "forest_enemy2.png", scale=(128, 128))
        self.load_image("lava_enemy2",   "lava_enemy2.png",   scale=(128, 128))
        self.load_image("ocean_enemy2",  "ocean_enemy2.png",  scale=(128, 128))
        self.load_image("ruins_enemy2",  "ruins_enemy2.png",  scale=(128, 128))
        # ── Tier 3 enemies ─────────────────────────────────────────────────────
        self.load_image("forest_enemy3", "forest_enemy3.png", scale=(128, 128))
        self.load_image("lava_enemy3",   "lava_enemy3.png",   scale=(128, 128))
        self.load_image("ocean_enemy3",  "ocean_enemy3.png",  scale=(128, 128))
        self.load_image("ruins_enemy3",  "ruins_enemy3.png",  scale=(128, 128))

        # ── Bosses ─────────────────────────────────────────────────────────────
        self.load_image("boss",        "boss.png",        scale=(128, 128))
        self.load_image("forest_boss", "forest_boss.png", scale=(128, 128))
        self.load_image("lava_boss",   "lava_boss.png",   scale=(128, 128))
        self.load_image("ocean_boss",  "ocean_boss.png",  scale=(128, 128))

        # ── NPC sprites ────────────────────────────────────────────────────────
        self.load_image("npc_elder",  "npc_elder.png",  scale=(80, 80))
        self.load_image("npc_fox",    "npc_fox.png",    scale=(80, 80))
        self.load_image("npc_scout",  "npc_scout.png",  scale=(80, 80))
        self.load_image("npc_turtle", "npc_turtle.png", scale=(80, 80))
        self.load_image("npc_ember",  "npc_ember.png",  scale=(80, 80))
        self.load_image("npc_sprite", "npc_sprite.png", scale=(80, 80))
        self.load_image("npc_hawk",   "npc_hawk.png",   scale=(80, 80))

        # ── Explore zone backgrounds ──────────────────────────────────────────
        self.load_image("explore_forest", "explore_forest.jpg", scale=(sw, sh))
        self.load_image("explore_lava",   "explore_lava.jpg",   scale=(sw, sh))
        self.load_image("explore_ocean",  "explore_ocean.jpg",  scale=(sw, sh))
        self.load_image("explore_ruins",  "explore_ruins.jpg",  scale=(sw, sh))

        # ── Shop item icons ────────────────────────────────────────────────────
        self.load_image("item_potion", "item_potion.png", scale=(64, 64))
        self.load_image("item_elixir", "item_elixir.png", scale=(64, 64))
        self.load_image("item_shield", "item_shield.png", scale=(64, 64))
        self.load_image("item_power",  "item_power.png",  scale=(64, 64))

        # ── UI icons ───────────────────────────────────────────────────────────
        self.load_image("icon_gold",   "icon_gold.png",   scale=(28, 28))

        # ── Sound effects ──────────────────────────────────────────────────────
        self.load_sound("attack",    "attack.ogg")
        self.load_sound("hit",       "hit.ogg")
        self.load_sound("victory",   "victory.ogg")
        self.load_sound("boss_sting","boss.ogg")
        self.load_sound("click",     "button-click-.ogg")
        self.load_sound("potion",    "potion.ogg")
        self.load_sound("story",     "story_chime.ogg")
        self.load_sound("evolution", "evolution.ogg")

        # ── Music (tries .ogg → .wav → .mp3 automatically) ───────────────────
        self.register_music("forest",  "forest")
        self.register_music("lava",    "lava")
        self.register_music("ocean",   "ocean")
        self.register_music("ruins",   "ruins")
        self.register_music("boss",    "boss_music")
        self.register_music("menu",    "menu_music")
        self.register_music("story",   "story_music")
        self.register_music("map",     "map_music")