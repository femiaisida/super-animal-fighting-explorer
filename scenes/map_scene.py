import pygame
import random
from core.scene_manager import Scene
from data.creatures import BIOME_DATA, make_enemy_party, make_random_enemy, restore_player
from systems.story import get_map_narration, get_npc_message
import systems.save_system as save_system

WINS_FOR_BOSS = 3

BIOMES = list(BIOME_DATA.keys())
TYPE_COLOURS = {
    "fire": (255,120,40), "water": (60,160,255),
    "nature": (80,210,80), None: (180,180,180),
}
RANDOM_ENCOUNTER_CHANCE = 0.35


class MapScene(Scene):
    def __init__(self, manager, assets, player_party=None,
                 player_character="hero", save_data=None, skip_npc=False):
        super().__init__(manager)
        self.assets           = assets
        self.player_character = player_character
        self.player_party     = player_party
        self.save_data        = save_data or save_system.load()
        self.sw               = assets.screen_w
        self.sh               = assets.screen_h
        self.selected         = 0
        self.show_shop        = False
        self._music_started   = False

        npc = get_npc_message(self.save_data)
        self.npc_name        = npc[0]
        self.npc_lines       = npc[1].split("\n")
        self.npc_sprite_key  = npc[2] if len(npc) > 2 else None
        self.npc_timer       = 0
        self.npc_auto_shown  = skip_npc

        boss_kills        = self.save_data.get("run_stats", {}).get("boss_kills", 0)
        self.narration    = get_map_narration(boss_kills)
        self.narr_index   = 0
        self.narr_timer   = 0

        self.pending_evo  = self.save_data.get("pending_evolution", False)

    def _cleared_boss(self, biome_key):
        return biome_key + "_boss" in self.save_data.get("cleared_biomes", [])

    def _cleared_normal(self, biome_key):
        return save_system.biome_win_count(self.save_data, biome_key) >= WINS_FOR_BOSS

    def handle_event(self, event):
        if self.show_shop:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(BIOMES)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(BIOMES)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._try_enter_biome(BIOMES[self.selected])
            elif event.key == pygame.K_s:
                self._open_shop()
            elif event.key == pygame.K_e and self.pending_evo:
                self._trigger_evolution()
            elif event.key == pygame.K_n:
                self._open_npc()
            elif event.key == pygame.K_x:
                self._open_explore()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._touch_start_x = event.pos[0]
            self._touch_moved   = False
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    if self.selected == i:
                        self._try_enter_biome(BIOMES[i])
                    else:
                        self.selected = i
                        self.assets.play_sound("click")
            if self._shop_rect().collidepoint(event.pos):
                self._open_shop()
            if self.pending_evo and self._evo_rect().collidepoint(event.pos):
                self._trigger_evolution()
            if self._npc_rect().collidepoint(event.pos):
                self._open_npc()
            if self._explore_rect().collidepoint(event.pos):
                self._open_explore()

        if event.type == pygame.MOUSEMOTION:
            if getattr(self, "_touch_start_x", None) is not None:
                dx = event.pos[0] - self._touch_start_x
                if abs(dx) > 30:
                    self._touch_moved = True
                    if dx < 0:
                        self.selected = (self.selected + 1) % len(BIOMES)
                    else:
                        self.selected = (self.selected - 1) % len(BIOMES)
                    self.assets.play_sound("click")
                    self._touch_start_x = event.pos[0]
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i

        if event.type == pygame.MOUSEBUTTONUP:
            self._touch_start_x = None
            self._touch_moved   = False

    def _open_npc(self):
        from scenes.npc_scene import NPCScene
        self.assets.play_sound("click")
        def back():
            self.manager.switch(MapScene(
                self.manager, self.assets,
                player_party=self.player_party,
                player_character=self.player_character,
                save_data=self.save_data,
                skip_npc=True,
            ))
        self.manager.switch(NPCScene(
            self.manager, self.assets,
            npc_name       = self.npc_name,
            npc_lines      = self.npc_lines,
            npc_sprite_key = self.npc_sprite_key,
            save_data      = self.save_data,
            on_close       = back,
        ))

    def _explore_rect(self):
        w, h = int(self.sw * 0.13), int(self.sh * 0.06)
        return pygame.Rect(int(self.sw * 0.41), int(self.sh * 0.88), w, h)

    def _open_explore(self):
        from scenes.explore_scene import ExploreScene
        self.assets.play_sound("click")
        self.manager.switch(ExploreScene(
            self.manager, self.assets,
            player_party=self.player_party,
            player_character=self.player_character,
            save_data=self.save_data,
        ))

    def _open_shop(self):
        from scenes.shop_scene import ShopScene
        self.assets.play_sound("click")
        self.manager.switch(ShopScene(
            self.manager, self.assets, self.save_data,
            on_close=lambda: self.manager.switch(MapScene(
                self.manager, self.assets,
                player_party=self.player_party,
                player_character=self.player_character,
                save_data=self.save_data,
            ))
        ))

    def _trigger_evolution(self):
        from scenes.evolution_scene import EvolutionScene
        self.assets.stop_music()
        def after_evo(new_save, new_party):
            self.manager.switch(MapScene(
                self.manager, self.assets,
                player_party=new_party,
                player_character=self.player_character,
                save_data=new_save,
            ))
        self.manager.switch(EvolutionScene(
            self.manager, self.assets,
            character=self.player_character,
            save_data=self.save_data,
            player_party=self.player_party,
            on_complete=after_evo,
        ))

    def _try_enter_biome(self, biome_key):
        self.assets.stop_music()
        if not self._cleared_boss(biome_key) and random.random() < RANDOM_ENCOUNTER_CHANCE:
            self._start_random_encounter()
            return
        self._start_biome(biome_key)

    def _start_random_encounter(self):
        from scenes.battle_scene import BattleScene
        from scenes.ambush_scene import AmbushScene
        from systems.battle_controller import BattleController
        from core.event_bus import EventBus

        evo_stage    = self.save_data.get("evolution_stage", 0)
        enemy_party  = make_random_enemy(evolution_stage=evo_stage)
        player_party = self._get_player_party()
        ambush_biome = BIOMES[self.selected]
        ambush_bg    = BIOME_DATA[ambush_biome]["bg_key"]
        biome_label  = BIOME_DATA[ambush_biome].get("label", ambush_biome.capitalize())

        def launch_battle():
            event_bus         = EventBus()
            battle_controller = BattleController(player_party, enemy_party, event_bus)
            self.manager.switch(BattleScene(
                manager=self.manager,
                player_party=player_party,
                enemy_party=enemy_party,
                battle_controller=battle_controller,
                assets=self.assets,
                bg_key=ambush_bg,
                biome_key=ambush_biome,
                is_boss_fight=False,
                is_random=True,
                player_character=self.player_character,
                save_data=self.save_data,
            ))

        self.manager.switch(AmbushScene(
            self.manager, self.assets,
            bg_key=ambush_bg,
            biome_name=biome_label,
            on_complete=launch_battle,
        ))

    def _start_biome(self, biome_key):
        from scenes.battle_scene import BattleScene
        from scenes.biome_intro_scene import BiomeIntroScene
        from systems.battle_controller import BattleController
        from core.event_bus import EventBus

        data        = BIOME_DATA[biome_key]
        evo_stage   = self.save_data.get("evolution_stage", 0)
        is_boss     = self._cleared_normal(biome_key)
        wins        = save_system.biome_win_count(self.save_data, biome_key)
        enemy_party = make_enemy_party(biome_key, is_boss=is_boss, evolution_stage=evo_stage, wins=wins)
        player_party = self._get_player_party()

        event_bus         = EventBus()
        battle_controller = BattleController(player_party, enemy_party, event_bus)
        self.assets.play_sound("click")

        def launch_battle():
            self.manager.switch(BattleScene(
                manager=self.manager,
                player_party=player_party,
                enemy_party=enemy_party,
                battle_controller=battle_controller,
                assets=self.assets,
                bg_key=data["bg_key"],
                biome_key=biome_key,
                is_boss_fight=is_boss,
                is_random=False,
                player_character=self.player_character,
                save_data=self.save_data,
            ))

        if biome_key not in self.save_data.get("visited_biomes", []):
            save_system.mark_biome_visited(self.save_data, biome_key)
            save_system.save(self.save_data)
            self.manager.switch(BiomeIntroScene(
                self.manager, self.assets, biome_key, on_complete=launch_battle
            ))
        else:
            launch_battle()

    def _get_player_party(self):
        if self.player_party:
            for c in self.player_party:
                c.alive = True
                for ab in c.abilities:
                    ab.current_cooldown = 0
            return self.player_party
        return [restore_player(self.player_character, self.save_data)]

    def update(self, dt):
        if not self._music_started:
            self._music_started = True
            self.assets.play_music("map")
        self.npc_timer  += 1
        self.narr_timer += 1

        if not self.npc_auto_shown and self.npc_timer > 5:
            self.npc_auto_shown = True
            self._open_npc()
            return

    def _card_rects(self):
        n       = len(BIOMES)
        card_w  = int(self.sw * 0.18)
        card_h  = int(self.sh * 0.50)
        gap     = int(self.sw * 0.025)
        total_w = n * card_w + (n - 1) * gap
        start_x = (self.sw - total_w) // 2
        card_y  = int(self.sh * 0.21)
        return [pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
                for i in range(n)]

    def _npc_rect(self):
        w, h = int(self.sw * 0.16), int(self.sh * 0.07)
        return pygame.Rect(int(self.sw * 0.20), int(self.sh * 0.875), w, h)

    def _shop_rect(self):
        w, h = int(self.sw * 0.13), int(self.sh * 0.07)
        return pygame.Rect(int(self.sw * 0.04), int(self.sh * 0.875), w, h)

    def _evo_rect(self):
        w, h = int(self.sw * 0.16), int(self.sh * 0.07)
        return pygame.Rect(int(self.sw * 0.57), int(self.sh * 0.875), w, h)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        lh     = int(sh / 54)   # base line height

        bg = self.assets.get_image(BIOME_DATA[BIOMES[self.selected]]["bg_key"])
        if bg:
            faded = bg.copy(); faded.set_alpha(100); screen.blit(faded, (0,0))
        else:
            screen.fill((10,10,20))

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0,0,0,155)); screen.blit(ov, (0,0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # ── Title ─────────────────────────────────────────────────────────
        if font_large:
            t  = font_large.render("WORLD MAP", True, (255, 220, 60))
            ts = font_large.render("WORLD MAP", True, (0,0,0))
            if t.get_width() > sw - 20:
                sc = (sw - 20) / t.get_width()
                t  = pygame.transform.scale(t,  (int(t.get_width()*sc), int(t.get_height()*sc)))
                ts = pygame.transform.scale(ts, (t.get_width(), t.get_height()))
            tx = cx - t.get_width() // 2
            screen.blit(ts, (tx+2, int(sh*0.03)+2))
            screen.blit(t,  (tx,   int(sh*0.03)))

        # ── HUD top-right: spaced lh*1.4 apart ───────────────────────────
        if font_small:
            gold  = self.save_data.get("gold", 0)
            pots  = self.save_data.get("potions", 0)
            level = self.save_data.get("level", 1)
            xp    = self.save_data.get("xp", 0)
            from systems.save_system import xp_for_next_level
            next_xp = xp_for_next_level(level)
            xp_str  = f"XP: {xp}/{next_xp}" if next_xp else "XP: MAX"
            hud_lines = [
                (f"Gold: {gold}g",    (255,200,50)),
                (f"Potions: {pots}",  (100,220,100)),
                (f"Lv.{level}",       (100,200,255)),
                (xp_str,              (140,180,220)),
            ]
            hud_y = int(sh * 0.03)
            for txt, col in hud_lines:
                s = font_small.render(txt, True, col)
                screen.blit(s, (sw - s.get_width() - 16, hud_y))
                hud_y += int(lh * 1.6)

        # ── Map narration ─────────────────────────────────────────────────
        if self.narration and font_small:
            import math
            fade = min(1.0, self.narr_timer / 60)
            line = self.narration[min(self.narr_index, len(self.narration)-1)]
            ns   = self.assets.render_fitted("small", line, (180, 160, 220), sw - 40)
            if ns:
                ns.set_alpha(int(255 * fade))
                screen.blit(ns, (cx - ns.get_width()//2, int(sh * 0.115)))

        # ── Progress ──────────────────────────────────────────────────────
        cleared = len([b for b in BIOMES if self._cleared_boss(b)])
        if font_small:
            prog = font_small.render(f"Seals restored: {cleared} / 4", True, (160,200,160))
            screen.blit(prog, (cx - prog.get_width()//2, int(sh*0.155)))

        # ── Biome cards ───────────────────────────────────────────────────
        rects = self._card_rects()
        for i, (biome_key, rect) in enumerate(zip(BIOMES, rects)):
            data      = BIOME_DATA[biome_key]
            selected  = (i == self.selected)
            b_done    = self._cleared_boss(biome_key)
            n_done    = self._cleared_normal(biome_key)
            wins_done = save_system.biome_win_count(self.save_data, biome_key)
            elem_col  = TYPE_COLOURS.get(data.get("element"), (180,180,180))

            cs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cs.fill((20,60,20,200) if b_done else (60,60,120,220) if selected else (20,20,40,200))
            screen.blit(cs, rect.topleft)

            brd = (100,220,100) if b_done else elem_col if selected else (80,80,100)
            pygame.draw.rect(screen, brd, rect, 3 if (selected or b_done) else 1, border_radius=12)

            # Thumbnail: top 46% of card
            thumb = self.assets.get_image(data["bg_key"])
            if thumb:
                th = int(rect.h * 0.44); tw = rect.w - 10
                ts = pygame.transform.scale(thumb, (tw, th))
                if b_done: ts.set_alpha(100)
                screen.blit(ts, (rect.x+5, rect.y+5))

            # Text section: starts at 50% of card height
            # Layout: label → lh*0 | element → lh*2.0 | status → lh*3.6 | boss → lh*5.2 | ENTER → bottom
            ty = rect.y + int(rect.h * 0.50)

            if font_medium:
                c   = (255,240,100) if selected else (200,200,200)
                lab = self.assets.render_fitted("medium", data["label"], c, rect.w - 10)
                if lab:
                    screen.blit(lab, (rect.x + rect.w//2 - lab.get_width()//2, ty))

            elem_y = ty + int(lh * 2.2)
            if font_small:
                el = self.assets.render_fitted("small",
                    (data.get("element") or "void").upper(), elem_col, rect.w - 10)
                if el:
                    screen.blit(el, (rect.x + rect.w//2 - el.get_width()//2, elem_y))

            status_y = elem_y + int(lh * 2.0)
            if font_small:
                if b_done:
                    s = self.assets.render_fitted("small", "✓ SEAL RESTORED", (100,255,100), rect.w - 10)
                elif n_done:
                    s = self.assets.render_fitted("small", "→ BOSS AWAITS!", (255,180,50), rect.w - 10)
                else:
                    s = self.assets.render_fitted("small", f"{wins_done}/{WINS_FOR_BOSS} wins",
                                                   (160,160,200), rect.w - 10)
                if s:
                    screen.blit(s, (rect.x + rect.w//2 - s.get_width()//2, status_y))

            boss_y = status_y + int(lh * 2.0)
            if font_small and not b_done:
                bs = self.assets.render_fitted("small", data["boss_name"], (220,100,60), rect.w - 10)
                if bs:
                    screen.blit(bs, (rect.x + rect.w//2 - bs.get_width()//2, boss_y))

            if selected and not b_done and font_small:
                hint = self.assets.render_fitted("small", "PRESS ENTER", (120,255,120), rect.w - 10)
                if hint:
                    screen.blit(hint, (rect.x + rect.w//2 - hint.get_width()//2,
                                       rect.bottom - int(lh * 1.6)))

        # ── Bottom buttons ────────────────────────────────────────────────
        sr = self._shop_rect()
        pygame.draw.rect(screen, (40,70,40), sr, border_radius=8)
        pygame.draw.rect(screen, (80,160,80), sr, 2, border_radius=8)
        if font_small:
            ss2 = self.assets.render_fitted("small", "[S] Shop", (180,240,180), sr.w - 12)
            if ss2:
                screen.blit(ss2, (sr.x + sr.w//2 - ss2.get_width()//2,
                                   sr.y + sr.h//2 - ss2.get_height()//2))

        if self.pending_evo:
            er = self._evo_rect()
            import math
            pulse = abs(math.sin(self.npc_timer * 0.05)) * 0.5 + 0.5
            ec    = (int(80*pulse+40), int(40*pulse+20), int(120*pulse+60))
            pygame.draw.rect(screen, ec, er, border_radius=8)
            pygame.draw.rect(screen, (180,100,255), er, 2, border_radius=8)
            if font_small:
                et = self.assets.render_fitted("small", "[E] EVOLVE NOW!", (220,160,255), er.w - 12)
                if et:
                    screen.blit(et, (er.x + er.w//2 - et.get_width()//2,
                                      er.y + er.h//2 - et.get_height()//2))

        # NPC button — two lines centred vertically
        nr       = self._npc_rect()
        npc_icon = self.assets.get_image(self.npc_sprite_key) if self.npc_sprite_key else None
        import math as _mth
        npc_pulse = abs(_mth.sin(self.npc_timer * 0.04)) * 0.4 + 0.6
        npc_bg    = (int(35*npc_pulse), int(20*npc_pulse), int(55*npc_pulse))
        pygame.draw.rect(screen, npc_bg, nr, border_radius=8)
        pygame.draw.rect(screen, (160, 100, 255), nr, 2, border_radius=8)
        if npc_icon:
            icon_sz = min(nr.h - 8, 28)
            icon24  = pygame.transform.scale(npc_icon, (icon_sz, icon_sz))
            screen.blit(icon24, (nr.x + 5, nr.y + nr.h//2 - icon_sz//2))
        if font_small:
            text_x  = nr.x + (38 if npc_icon else 8)
            avail_w = nr.w - (text_x - nr.x) - 4
            nl1 = self.assets.render_fitted("small", "[N] Talk to", (200, 160, 255), avail_w)
            nl2 = self.assets.render_fitted("small", self.npc_name,  (230, 200, 255), avail_w)
            # Stack both lines centred in button height
            total_h = (nl1.get_height() if nl1 else 0) + int(lh * 0.4) + (nl2.get_height() if nl2 else 0)
            line_top = nr.y + nr.h // 2 - total_h // 2
            if nl1:
                screen.blit(nl1, (text_x, line_top))
            if nl2:
                screen.blit(nl2, (text_x, line_top + (nl1.get_height() if nl1 else 0) + int(lh * 0.4)))

        xr = self._explore_rect()
        pygame.draw.rect(screen, (20, 50, 60), xr, border_radius=8)
        pygame.draw.rect(screen, (60, 180, 220), xr, 2, border_radius=8)
        if font_small:
            xl = self.assets.render_fitted("small", "[X] Explore", (80, 210, 255), xr.w - 12)
            if xl:
                screen.blit(xl, (xr.x + xr.w // 2 - xl.get_width() // 2,
                                  xr.y + xr.h // 2 - xl.get_height() // 2))

        # Nav hint
        if font_small:
            nav = self.assets.render_fitted("small",
                "← → browse   ENTER fight   S shop   X explore   N talk",
                (100,100,130), sw - 20)
            if nav:
                screen.blit(nav, (cx - nav.get_width()//2, int(sh*0.958)))

    def _draw_npc(self, screen, font_small, font_medium):
        sw, sh  = self.sw, self.sh
        fade    = min(1.0, self.npc_timer / 80)
        alpha   = int(210 * fade)

        sprite_img = self.assets.get_image(self.npc_sprite_key) if self.npc_sprite_key else None
        has_sprite = sprite_img is not None
        pw = int(sw * 0.30) + (78 if has_sprite else 0)
        ph = int(sh * 0.20)
        px = sw - pw - 20
        py = int(sh * 0.67)

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 16, 34, alpha))
        screen.blit(panel, (px, py))
        border = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(border, (95, 70, 155, alpha), (0, 0, pw, ph), 2, border_radius=10)
        screen.blit(border, (px, py))

        text_x = px + 10
        if sprite_img:
            spr72 = pygame.transform.scale(sprite_img, (72, 72))
            spr72.set_alpha(alpha)
            screen.blit(spr72, (px + 6, py + ph // 2 - 36))
            text_x = px + 86

        lh = int(sh / 54)
        if font_small:
            nm = font_small.render(self.npc_name, True, (200, 155, 255))
            nm.set_alpha(alpha)
            screen.blit(nm, (text_x, py + 10))
            words = self.npc_line.split("\n")
            for j, word_line in enumerate(words[:3]):
                ls = font_small.render(word_line, True, (188, 188, 205))
                ls.set_alpha(alpha)
                screen.blit(ls, (text_x, py + 10 + int(lh * 1.8) * (j + 1)))