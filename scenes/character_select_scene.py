import pygame
import math
from core.scene_manager import Scene
from data.creatures import CHARACTER_DATA
import systems.save_system as save_system

CHARACTERS = ["fire", "water", "nature", "void"]

CHARACTER_DESC = {
    "fire":   ["Fast attacker", "Burns enemies over time", "Weak vs Water biomes"],
    "water":  ["Balanced fighter", "High HP pool", "Weak vs Nature biomes"],
    "nature": ["Status specialist", "Persistent DoT", "Weak vs Fire biomes"],
    "void":   ["True damage — ignores type", "Drain heals on hit", "No strengths or weaknesses"],
}

TYPE_COLOURS = {
    "fire":   (255, 120,  40),
    "water":  ( 60, 160, 255),
    "nature": ( 80, 210,  80),
    "void":   (160,  80, 255),
}


class CharacterSelectScene(Scene):
    def __init__(self, manager, assets):
        super().__init__(manager)
        self.assets    = assets
        self.selected  = 0
        info           = pygame.display.Info()
        self.sw        = info.current_w
        self.sh        = info.current_h
        self.anim_time = 0.0
        self.save_data = save_system.load()
        self.has_save  = bool(self.save_data.get("cleared_biomes"))
        # Ensure menu music is playing (may arrive from loading scene or continue)
        self.assets.play_music("menu")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected = (self.selected - 1) % len(CHARACTERS)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected = (self.selected + 1) % len(CHARACTERS)
                self.assets.play_sound("click")
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_new(CHARACTERS[self.selected])
            elif event.key == pygame.K_c and self.has_save:
                self._continue_run()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                import sys; sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    if self.selected == i:
                        self._start_new(CHARACTERS[i])
                    else:
                        self.selected = i
                        self.assets.play_sound("click")
            if self.has_save and self._continue_rect().collidepoint(event.pos):
                self._continue_run()

        if event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._card_rects()):
                if rect.collidepoint(event.pos):
                    self.selected = i

    def _start_new(self, character):
        from scenes.story_intro_scene import StoryIntroScene
        from data.creatures import make_player
        save_data = save_system.new_run(character)
        save_system.save(save_data)
        player    = make_player(character)

        def go_to_map():
            from scenes.map_scene import MapScene
            self.manager.switch(MapScene(
                self.manager, self.assets,
                player_party=[player],
                player_character=character,
                save_data=save_data,
            ))
        self.manager.switch(StoryIntroScene(
            self.manager, self.assets, character, on_complete=go_to_map
        ))

    def _continue_run(self):
        from scenes.map_scene import MapScene
        from data.creatures import restore_player
        sd        = self.save_data
        character = sd.get("player_character", "hero")
        player    = restore_player(character, sd)
        self.manager.switch(MapScene(
            self.manager, self.assets,
            player_party=[player],
            player_character=character,
            save_data=sd,
        ))

    def update(self, dt):
        self.anim_time += dt

    def _card_rects(self):
        n       = len(CHARACTERS)
        card_w  = int(self.sw * 0.17)
        card_h  = int(self.sh * 0.58)
        gap     = int(self.sw * 0.025)
        total_w = n * card_w + (n - 1) * gap
        start_x = (self.sw - total_w) // 2
        card_y  = int(self.sh * 0.18)
        return [pygame.Rect(start_x + i * (card_w + gap), card_y, card_w, card_h)
                for i in range(n)]

    def _continue_rect(self):
        w, h = 400, 50
        return pygame.Rect(self.sw // 2 - w // 2, int(self.sh * 0.88), w, h)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        bg = self.assets.get_image("selection_bg")
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((10, 10, 25))

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 130))
        screen.blit(ov, (0, 0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        if font_large:
            t  = font_large.render("CHOOSE YOUR FIGHTER", True, (255, 220, 60))
            ts = font_large.render("CHOOSE YOUR FIGHTER", True, (0, 0, 0))
            tx = sw // 2 - t.get_width() // 2
            screen.blit(ts, (tx + 2, int(sh * 0.06) + 2))
            screen.blit(t,  (tx,     int(sh * 0.06)))

        if font_small:
            sub = font_small.render(
                "The prophecy has chosen you. Who will answer the call?",
                True, (160, 140, 200))
            screen.blit(sub, (sw // 2 - sub.get_width() // 2, int(sh * 0.12)))

        rects = self._card_rects()
        for i, char in enumerate(CHARACTERS):
            rect     = rects[i]
            selected = (i == self.selected)
            data     = CHARACTER_DATA[char]
            col      = TYPE_COLOURS[char]
            bob      = int(math.sin(self.anim_time * 3.0) * 8) if selected else 0
            dr       = pygame.Rect(rect.x, rect.y + bob, rect.w, rect.h)

            # Card bg
            cs = pygame.Surface((dr.w, dr.h), pygame.SRCALPHA)
            cs.fill((*col[:3], 50) if selected else (18, 18, 38, 210))
            screen.blit(cs, dr.topleft)
            pygame.draw.rect(screen, col if selected else (70, 70, 100),
                             dr, 3 if selected else 1, border_radius=14)

            # Sprite — 200px selected, 160px unselected
            sprite = self.assets.get_image(data["stages"][0]["img"])
            if sprite:
                sz  = (150, 150) if selected else (120, 120)
                img = pygame.transform.scale(sprite, sz)
                sx  = dr.x + dr.w // 2 - sz[0] // 2
                sy  = dr.y + int(dr.h * 0.04)
                screen.blit(img, (sx, sy))
            else:
                fb_sz = (140, 140) if selected else (110, 110)
                fb_r  = pygame.Rect(dr.x + dr.w // 2 - fb_sz[0] // 2, dr.y + 10, *fb_sz)
                pygame.draw.rect(screen, (*col[:3], 100), fb_r, border_radius=10)

            # Text — starts below sprite
            ty = dr.y + int(dr.h * 0.65)

            base_stage = data["stages"][0]
            if font_medium:
                ns = font_medium.render(base_stage["name"], True, col if selected else (200, 200, 200))
                screen.blit(ns, (dr.x + dr.w // 2 - ns.get_width() // 2, ty))

            if font_small:
                el = font_small.render(char.upper(), True, col)
                screen.blit(el, (dr.x + dr.w // 2 - el.get_width() // 2, ty + 22))

                if selected:
                    for j, line in enumerate(CHARACTER_DESC.get(char, [])):
                        ls = font_small.render(line, True, (185, 185, 185))
                        screen.blit(ls, (dr.x + 8, ty + 46 + j * 17))

                hp_s = font_small.render(f"HP: {base_stage['hp']}", True, (100, 210, 100))
                screen.blit(hp_s, (dr.x + 8, dr.bottom - 22))

            if selected and font_small:
                hint = font_small.render("PRESS ENTER", True, (120, 255, 120))
                screen.blit(hint, (dr.x + dr.w // 2 - hint.get_width() // 2, dr.bottom - 40))

        if self.has_save:
            cr = self._continue_rect()
            pygame.draw.rect(screen, (35, 70, 35), cr, border_radius=8)
            pygame.draw.rect(screen, (75, 175, 75), cr, 2, border_radius=8)
            if font_small:
                sc   = self.save_data.get("player_character", "?").upper()
                cl   = len([b for b in self.save_data.get("cleared_biomes", [])
                             if not b.endswith("_normal") and not b.endswith("_boss")])
                gold = self.save_data.get("gold", 0)
                ct   = font_small.render(
                    f"[C] CONTINUE  ({sc}  •  {cl}/4 seals  •  {gold}g)",
                    True, (175, 255, 175))
                screen.blit(ct, (cr.x + cr.w // 2 - ct.get_width() // 2,
                                 cr.y + cr.h // 2 - ct.get_height() // 2))

        if font_small:
            nav = font_small.render(
                "← → browse   ENTER select   C continue   ESC quit",
                True, (90, 90, 120))
            screen.blit(nav, (sw // 2 - nav.get_width() // 2, int(sh * 0.95)))