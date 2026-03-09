"""
Explore Scene — a safe training/grinding area where the player fights
random enemies for gold without any boss encounter risk.
Accessible from the world map at any time.
"""
import pygame
import random
import math
from core.scene_manager import Scene
from data.creatures import BIOME_DATA, make_explore_enemy, restore_player
import systems.save_system as save_system

EXPLORE_BIOMES = [
    {"key": "forest", "label": "Wildwood Trail",
     "desc": "Tangle with forest creatures.",   "bg": "explore_forest", "music": "forest"},
    {"key": "lava",   "label": "Ember Foothills",
     "desc": "Skirmish near the volcano base.", "bg": "explore_lava",   "music": "lava"},
    {"key": "ocean",  "label": "Shallows",
     "desc": "Wade through coastal brawls.",    "bg": "explore_ocean",  "music": "ocean"},
    {"key": "ruins",  "label": "Outer Ruins",
     "desc": "Scout the crumbling outskirts.",  "bg": "explore_ruins",  "music": "ruins"},
]


class ExploreScene(Scene):
    def __init__(self, manager, assets, player_party=None,
                 player_character="hero", save_data=None):
        super().__init__(manager)
        self.assets           = assets
        self.player_party     = player_party
        self.player_character = player_character
        self.save_data        = save_data or save_system.load()

        self.sw = assets.screen_w
        self.sh = assets.screen_h

        self.selected  = 0
        self.timer     = 0
        self.fade_in   = 0.0
        self._music_started = False

    def escape_quits(self):
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(EXPLORE_BIOMES)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(EXPLORE_BIOMES)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_fight()
            elif event.key == pygame.K_ESCAPE:
                self._back_to_map()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._touch_start_x = event.pos[0]
            self._touch_moved   = False
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    if self.selected == i:
                        self._start_fight()
                    else:
                        self.selected = i
                        self.assets.play_sound("click")
            if self._back_rect().collidepoint(event.pos):
                self._back_to_map()

        if event.type == pygame.MOUSEMOTION:
            if getattr(self, "_touch_start_x", None) is not None:
                dx = event.pos[0] - self._touch_start_x
                if abs(dx) > 30:
                    self._touch_moved = True
                    if dx < 0:
                        self.selected = (self.selected + 1) % len(EXPLORE_BIOMES)
                    else:
                        self.selected = (self.selected - 1) % len(EXPLORE_BIOMES)
                    self.assets.play_sound("click")
                    self._touch_start_x = event.pos[0]
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i

        if event.type == pygame.MOUSEBUTTONUP:
            self._touch_start_x = None
            self._touch_moved   = False

    def _back_to_map(self):
        from scenes.map_scene import MapScene
        self.assets.play_sound("click")
        self.manager.switch(MapScene(
            self.manager, self.assets,
            player_party=self.player_party,
            player_character=self.player_character,
            save_data=self.save_data,
            skip_npc=True,
        ))

    def _start_fight(self):
        from scenes.battle_scene import BattleScene
        from systems.battle_controller import BattleController
        from core.event_bus import EventBus

        biome       = EXPLORE_BIOMES[self.selected]
        evo_stage   = self.save_data.get("evolution_stage", 0)
        enemy_party = make_explore_enemy(evolution_stage=evo_stage)
        if self.player_party:
            player_party = self.player_party
        else:
            player_party = [restore_player(self.player_character, self.save_data)]

        event_bus         = EventBus()
        battle_controller = BattleController(player_party, enemy_party, event_bus)
        self.assets.play_sound("click")

        self.manager.switch(BattleScene(
            manager=self.manager,
            player_party=player_party,
            enemy_party=enemy_party,
            battle_controller=battle_controller,
            assets=self.assets,
            bg_key=biome["bg"],
            biome_key=biome["key"],
            is_boss_fight=False,
            is_random=True,
            player_character=self.player_character,
            save_data=self.save_data,
            origin="explore",
        ))

    def update(self, dt):
        if not self._music_started:
            self._music_started = True
            self.assets.play_music("map")
        self.timer  += 1
        self.fade_in = min(1.0, self.fade_in + dt * 2.5)

    def _card_rects(self):
        n       = len(EXPLORE_BIOMES)
        card_w  = int(self.sw * 0.19)
        card_h  = int(self.sh * 0.50)
        gap     = int(self.sw * 0.025)
        total_w = n * card_w + (n - 1) * gap
        start_x = (self.sw - total_w) // 2
        card_y  = int(self.sh * 0.23)
        return [pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
                for i in range(n)]

    def _back_rect(self):
        w, h = int(self.sw * 0.14), int(self.sh * 0.065)
        return pygame.Rect(int(self.sw * 0.04), int(self.sh * 0.875), w, h)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        alpha  = int(255 * self.fade_in)
        lh     = int(sh / 54)

        biome = EXPLORE_BIOMES[self.selected]
        bg    = self.assets.get_image(biome["bg"])
        if bg:
            faded = bg.copy(); faded.set_alpha(90); screen.blit(faded, (0, 0))
        else:
            screen.fill((8, 12, 22))

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160)); screen.blit(ov, (0, 0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # Title
        if font_large:
            t  = font_large.render("EXPLORE", True, (100, 220, 255))
            ts = font_large.render("EXPLORE", True, (0, 0, 0))
            if t.get_width() > sw - 20:
                sc = (sw - 20) / t.get_width()
                t  = pygame.transform.scale(t,  (int(t.get_width()*sc), int(t.get_height()*sc)))
                ts = pygame.transform.scale(ts, (t.get_width(), t.get_height()))
            t.set_alpha(alpha); ts.set_alpha(alpha // 2)
            tx = cx - t.get_width() // 2
            screen.blit(ts, (tx + 2, int(sh * 0.04) + 2))
            screen.blit(t,  (tx,     int(sh * 0.04)))

        # Subtitle
        if font_small:
            sub = self.assets.render_fitted("small", "Fight for gold — no bosses",
                                            (140, 200, 180), sw - 40)
            if sub:
                sub.set_alpha(alpha)
                screen.blit(sub, (cx - sub.get_width() // 2, int(sh * 0.115)))

        # HUD top-right — spaced lh*1.6 apart
        if font_small:
            gold = self.save_data.get("gold", 0)
            pots = self.save_data.get("potions", 0)
            hud_y = int(sh * 0.04)
            for txt, col in [(f"Gold: {gold}g", (255,200,50)), (f"Potions: {pots}", (100,220,100))]:
                s = font_small.render(txt, True, col)
                screen.blit(s, (sw - s.get_width() - 16, hud_y))
                hud_y += int(lh * 1.6)

        # Zone cards
        rects = self._card_rects()
        for i, (zone, rect) in enumerate(zip(EXPLORE_BIOMES, rects)):
            selected = (i == self.selected)
            pulse    = abs(math.sin(self.timer * 0.04 + i)) * 0.3 + 0.7

            cs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cs.fill((40, 80, 100, 220) if selected else (20, 30, 50, 200))
            screen.blit(cs, rect.topleft)

            brd_col = (80, 200, 255) if selected else (50, 80, 110)
            pygame.draw.rect(screen, brd_col, rect, 3 if selected else 1, border_radius=10)

            # Thumbnail: top 44% of card
            thumb = self.assets.get_image(zone["bg"])
            if thumb:
                th  = int(rect.h * 0.43); tw = rect.w - 10
                ts2 = pygame.transform.scale(thumb, (tw, th))
                if not selected: ts2.set_alpha(140)
                screen.blit(ts2, (rect.x + 5, rect.y + 5))

            # Text section: 47% down
            # label → text_top | desc lines → lh*2.0 each | ENTER → bottom
            text_top = rect.y + int(rect.h * 0.47)
            inner_w  = rect.w - 12

            if font_medium:
                lbl = self.assets.render_fitted("medium", zone["label"],
                    (100, 220, 255) if selected else (160, 180, 200), inner_w)
                if lbl:
                    screen.blit(lbl, (rect.x + rect.w//2 - lbl.get_width()//2, text_top))

            desc_y = text_top + int(lh * 2.2)
            if font_small:
                # Word-wrap description
                words = zone["desc"].split()
                lines_out, cur = [], ""
                for w in words:
                    test = (cur + " " + w).strip()
                    if font_small.size(test)[0] <= inner_w:
                        cur = test
                    else:
                        if cur: lines_out.append(cur)
                        cur = w
                if cur: lines_out.append(cur)
                for dl in lines_out[:2]:
                    ds = font_small.render(dl, True, (160, 180, 190))
                    screen.blit(ds, (rect.x + rect.w//2 - ds.get_width()//2, desc_y))
                    desc_y += int(lh * 1.8)

            if selected and font_small:
                hint = self.assets.render_fitted("small", "ENTER to fight",
                                                  (80, 220, 255), inner_w)
                if hint:
                    pulse_a = int(200 * pulse)
                    hint.set_alpha(pulse_a)
                    screen.blit(hint, (rect.x + rect.w//2 - hint.get_width()//2,
                                       rect.bottom - int(lh * 1.6)))

        # Back button
        br = self._back_rect()
        pygame.draw.rect(screen, (30, 30, 50), br, border_radius=7)
        pygame.draw.rect(screen, (80, 80, 120), br, 1, border_radius=7)
        if font_small:
            bl = self.assets.render_fitted("small", "[ESC] Back", (160, 160, 200), br.w - 10)
            if bl:
                screen.blit(bl, (br.x + br.w//2 - bl.get_width()//2,
                                  br.y + br.h//2 - bl.get_height()//2))

        # Nav hint
        if font_small:
            nav = self.assets.render_fitted("small", "← → browse zones   ENTER fight",
                                            (80, 90, 120), sw - 20)
            if nav:
                screen.blit(nav, (cx - nav.get_width()//2, int(sh * 0.958)))

        # Fade-in overlay
        if self.fade_in < 1.0:
            fo = pygame.Surface((sw, sh), pygame.SRCALPHA)
            fo.fill((0, 0, 0, int(255 * (1.0 - self.fade_in))))
            screen.blit(fo, (0, 0))