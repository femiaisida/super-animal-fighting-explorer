import pygame
import random
from core.scene_manager import Scene
from data.creatures import BIOME_DATA, make_enemy_party, make_random_enemy, restore_player
from systems.story import get_map_narration, get_npc_message
import systems.save_system as save_system

WINS_FOR_BOSS = 3   # normal wins required before boss spawns

BIOMES = list(BIOME_DATA.keys())
TYPE_COLOURS = {
    "fire": (255,120,40), "water": (60,160,255),
    "nature": (80,210,80), None: (180,180,180),
}
RANDOM_ENCOUNTER_CHANCE = 0.35   # 35% on biome select


class MapScene(Scene):
    def __init__(self, manager, assets, player_party=None,
                 player_character="hero", save_data=None, skip_npc=False):
        super().__init__(manager)
        self.assets           = assets
        self.player_character = player_character
        self.player_party     = player_party
        self.save_data        = save_data or save_system.load()
        info                  = pygame.display.Info()
        self.sw               = info.current_w
        self.sh               = info.current_h
        self.selected         = 0
        self.show_shop        = False

        # Play map exploration music
        self._music_started = False

        # NPC — always present, auto-launches on entry
        npc = get_npc_message(self.save_data)
        self.npc_name        = npc[0]
        self.npc_lines       = npc[1].split("\n")
        self.npc_sprite_key  = npc[2] if len(npc) > 2 else None
        self.npc_timer       = 0
        self.npc_auto_shown  = skip_npc   # skip_npc=True means don't auto-open

        # Map narration
        boss_kills        = self.save_data.get("run_stats", {}).get("boss_kills", 0)
        self.narration    = get_map_narration(boss_kills)
        self.narr_index   = 0
        self.narr_timer   = 0

        # Pending evolution check
        self.pending_evo  = self.save_data.get("pending_evolution", False)

    def _cleared_boss(self, biome_key):
        return biome_key + "_boss" in self.save_data.get("cleared_biomes", [])

    def _cleared_normal(self, biome_key):
        """True if player has enough wins to face the boss."""
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
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i

    def _open_npc(self):
        from scenes.npc_scene import NPCScene
        self.assets.play_sound("click")
        def back():
            self.manager.switch(MapScene(
                self.manager, self.assets,
                player_party=self.player_party,
                player_character=self.player_character,
                save_data=self.save_data,
                skip_npc=True,   # don't re-trigger NPC on return
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
        self.assets.stop_music()   # silence map music during evolution
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
        self.assets.stop_music()   # always silence map music before any battle path
        # Random encounter check (not on cleared biomes)
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
                biome_key=ambush_biome,   # pass biome so battle plays biome music
                is_boss_fight=False,
                is_random=True,           # is_random=True means no biome progress tracked
                player_character=self.player_character,
                save_data=self.save_data,
            ))

        # Show ambush warning first
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

        # Show biome intro if first visit
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

        # Auto-launch NPC interaction on first map entry
        if not self.npc_auto_shown and self.npc_timer > 5:
            self.npc_auto_shown = True
            self._open_npc()
            return

    def _card_rects(self):
        n       = len(BIOMES)
        card_w  = int(self.sw * 0.18)
        card_h  = int(self.sh * 0.48)
        gap     = int(self.sw * 0.025)
        total_w = n * card_w + (n - 1) * gap
        start_x = (self.sw - total_w) // 2
        card_y  = int(self.sh * 0.22)
        return [pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
                for i in range(n)]

    def _npc_rect(self):
        w, h = int(self.sw * 0.16), int(self.sh * 0.06)
        return pygame.Rect(int(self.sw * 0.20), int(self.sh * 0.88), w, h)

    def _shop_rect(self):
        w, h = int(self.sw * 0.13), int(self.sh * 0.06)
        return pygame.Rect(int(self.sw * 0.04), int(self.sh * 0.88), w, h)

    def _evo_rect(self):
        w, h = int(self.sw * 0.16), int(self.sh * 0.06)
        return pygame.Rect(int(self.sw * 0.57), int(self.sh * 0.88), w, h)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2

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

        # Title
        if font_large:
            t  = font_large.render("WORLD MAP", True, (255, 220, 60))
            ts = font_large.render("WORLD MAP", True, (0,0,0))
            tx = cx - t.get_width() // 2
            screen.blit(ts, (tx+2, int(sh*0.05)+2)); screen.blit(t, (tx, int(sh*0.05)))

        # HUD — gold, potions, level, XP
        if font_small:
            gold  = self.save_data.get("gold", 0)
            pots  = self.save_data.get("potions", 0)
            level = self.save_data.get("level", 1)
            xp    = self.save_data.get("xp", 0)
            # XP to next level
            from systems.save_system import xp_for_next_level, XP_PER_LEVEL
            next_xp = xp_for_next_level(level)
            xp_str  = f"XP: {xp}/{next_xp}" if next_xp else "XP: MAX"
            gs  = font_small.render(f"Gold: {gold}g", True, (255,200,50))
            ps  = font_small.render(f"Potions: {pots}", True, (100,220,100))
            lvs = font_small.render(f"Lv.{level}", True, (100, 200, 255))
            xs  = font_small.render(xp_str, True, (140, 180, 220))
            screen.blit(gs,  (sw - gs.get_width()  - 20, 20))
            screen.blit(ps,  (sw - ps.get_width()  - 20, 38))
            screen.blit(lvs, (sw - lvs.get_width() - 20, 56))
            screen.blit(xs,  (sw - xs.get_width()  - 20, 74))

        # Map narration
        if self.narration and font_small:
            import math
            fade = min(1.0, self.narr_timer / 60)
            line = self.narration[min(self.narr_index, len(self.narration)-1)]
            ns   = font_small.render(line, True, (180, 160, 220))
            ns.set_alpha(int(255 * fade))
            screen.blit(ns, (cx - ns.get_width()//2, int(sh * 0.135)))

        # Progress
        cleared = len([b for b in BIOMES if self._cleared_boss(b)])
        if font_small:
            prog = font_small.render(f"Seals restored: {cleared} / 4", True, (160,200,160))
            screen.blit(prog, (cx - prog.get_width()//2, int(sh*0.165)))

        # Biome cards
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

            thumb = self.assets.get_image(data["bg_key"])
            if thumb:
                th = int(rect.h * 0.44); tw = rect.w - 10
                ts = pygame.transform.scale(thumb, (tw, th))
                if b_done: ts.set_alpha(100)
                screen.blit(ts, (rect.x+5, rect.y+5))

            ty = rect.y + int(rect.h * 0.52)
            if font_medium:
                c   = (255,240,100) if selected else (200,200,200)
                lab = font_medium.render(data["label"], True, c)
                screen.blit(lab, (rect.x + rect.w//2 - lab.get_width()//2, ty))

            if font_small:
                el  = font_small.render((data.get("element") or "void").upper(), True, elem_col)
                screen.blit(el, (rect.x + rect.w//2 - el.get_width()//2, ty+22))

                if b_done:
                    s = font_small.render("✓ SEAL RESTORED", True, (100,255,100))
                elif n_done:
                    s = font_small.render("→ BOSS AWAITS!", True, (255,180,50))
                else:
                    s = font_small.render(f"{wins_done}/{WINS_FOR_BOSS} wins", True, (160,160,200))
                screen.blit(s, (rect.x+6, ty+44))

                if not b_done:
                    bs = font_small.render(data["boss_name"], True, (220,100,60))
                    screen.blit(bs, (rect.x+6, ty+62))

            if selected and not b_done and font_small:
                hint = font_small.render("PRESS ENTER", True, (120,255,120))
                screen.blit(hint, (rect.x + rect.w//2 - hint.get_width()//2, rect.bottom-28))

        # Shop button
        sr = self._shop_rect()
        pygame.draw.rect(screen, (40,70,40), sr, border_radius=8)
        pygame.draw.rect(screen, (80,160,80), sr, 2, border_radius=8)
        if font_small:
            ss2 = font_small.render("[S] Shop", True, (180,240,180))
            screen.blit(ss2, (sr.x + sr.w//2 - ss2.get_width()//2,
                               sr.y + sr.h//2 - ss2.get_height()//2))

        # Evolution button
        if self.pending_evo:
            er = self._evo_rect()
            import math
            pulse = abs(math.sin(self.npc_timer * 0.05)) * 0.5 + 0.5
            ec    = (int(80*pulse+40), int(40*pulse+20), int(120*pulse+60))
            pygame.draw.rect(screen, ec, er, border_radius=8)
            pygame.draw.rect(screen, (180,100,255), er, 2, border_radius=8)
            if font_small:
                et = font_small.render("[E] EVOLVE NOW!", True, (220,160,255))
                screen.blit(et, (er.x + er.w//2 - et.get_width()//2,
                                  er.y + er.h//2 - et.get_height()//2))

        # ── NPC button — always present, prominent ───────────────────────
        nr       = self._npc_rect()
        npc_icon = self.assets.get_image(self.npc_sprite_key) if self.npc_sprite_key else None
        import math as _mth
        npc_pulse = abs(_mth.sin(self.npc_timer * 0.04)) * 0.4 + 0.6
        npc_bg    = (int(35*npc_pulse), int(20*npc_pulse), int(55*npc_pulse))
        pygame.draw.rect(screen, npc_bg, nr, border_radius=8)
        pygame.draw.rect(screen, (160, 100, 255), nr, 2, border_radius=8)
        if npc_icon:
            icon24 = pygame.transform.scale(npc_icon, (28, 28))
            screen.blit(icon24, (nr.x + 6, nr.y + nr.h//2 - 14))
        if font_small:
            label_x = nr.x + (38 if npc_icon else 8)
            nl1 = font_small.render("[N] Talk to", True, (200, 160, 255))
            nl2 = font_small.render(self.npc_name, True, (230, 200, 255))
            screen.blit(nl1, (label_x, nr.y + 5))
            screen.blit(nl2, (label_x, nr.y + nr.h//2 + 2))

        # Explore button
        xr = self._explore_rect()
        pygame.draw.rect(screen, (20, 50, 60), xr, border_radius=8)
        pygame.draw.rect(screen, (60, 180, 220), xr, 2, border_radius=8)
        if font_small:
            xl = font_small.render("[X] Explore", True, (80, 210, 255))
            screen.blit(xl, (xr.x + xr.w // 2 - xl.get_width() // 2,
                              xr.y + xr.h // 2 - xl.get_height() // 2))

        # Nav hint
        if font_small:
            nav = font_small.render(
                "← → browse   ENTER fight   S shop   X explore   N talk",
                True, (100,100,130))
            screen.blit(nav, (cx - nav.get_width()//2, int(sh*0.95)))

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

        if font_small:
            nm = font_small.render(self.npc_name, True, (200, 155, 255))
            nm.set_alpha(alpha)
            screen.blit(nm, (text_x, py + 10))
            words = self.npc_line.split("\n")
            for j, word_line in enumerate(words[:3]):
                ls = font_small.render(word_line, True, (188, 188, 205))
                ls.set_alpha(alpha)
                screen.blit(ls, (text_x, py + 28 + j * 18))