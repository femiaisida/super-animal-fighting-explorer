import pygame
import math
from core.scene_manager import Scene


class LoadingScene(Scene):
    def __init__(self, manager, assets):
        super().__init__(manager)
        self.assets         = assets
        self.sw             = assets.screen_w
        self.sh             = assets.screen_h
        self.timer          = 0
        self.fade_in        = 0.0
        self.fade_out       = 0.0
        self.leaving        = False
        self._music_started = False
        self._ready         = False

    def handle_event(self, event):
        if not self._ready:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._start_leave()

    def _start_leave(self):
        if not self.leaving:
            self.leaving = True
            self.assets.play_sound("click")
            # Start music here — inside a user gesture handler so mobile
            # browsers unlock the audio context before any other scene plays
            if not self._music_started:
                self._music_started = True
                self.assets.play_music("menu")

    def _go(self):
        from scenes.character_select_scene import CharacterSelectScene
        self.manager.switch(CharacterSelectScene(self.manager, self.assets))

    def update(self, dt):
        # Music now starts in _start_leave() on first user gesture instead
        self.timer   += 1
        self.fade_in  = min(1.0, self.fade_in + dt * 1.2)
        if self.fade_in >= 1.0:
            self._ready = True
        if self.leaving:
            self.fade_out = min(1.0, self.fade_out + dt * 3.0)
            if self.fade_out >= 1.0:
                self._go()

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx, cy = sw // 2, sh // 2
        screen.fill((4, 4, 14))

        for i in range(120):
            bx = int((math.sin(i * 137.508) * 0.5 + 0.5) * sw)
            by = int((math.cos(i * 137.508) * 0.5 + 0.5) * sh)
            twinkle = abs(math.sin(self.timer * 0.03 + i)) * 0.6 + 0.4
            a = int(80 * twinkle * self.fade_in)
            if a > 0:
                s = pygame.Surface((3, 3), pygame.SRCALPHA)
                pygame.draw.circle(s, (180, 180, 255, a), (1, 1), 1)
                screen.blit(s, (bx, by))

        alpha      = int(255 * self.fade_in)
        title_y    = int(sh * 0.42)
        line_gap   = int(sh * 0.07)
        top_line_y = title_y - int(sh * 0.12)
        bot_line_y = title_y + int(sh * 0.13)
        credit_y   = title_y + int(sh * 0.18)
        subtitle_y = top_line_y + int(sh * 0.03)

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        def clamp_surf(surf, max_w):
            if surf.get_width() > max_w:
                scale = max_w / surf.get_width()
                return pygame.transform.scale(surf, (int(surf.get_width() * scale), int(surf.get_height() * scale)))
            return surf

        if self.fade_in > 0.3:
            line_a = int(180 * min(1.0, (self.fade_in - 0.3) * 2))
            ls = pygame.Surface((int(sw * 0.6), 1), pygame.SRCALPHA)
            ls.fill((120, 100, 220, line_a))
            screen.blit(ls, (cx - ls.get_width() // 2, top_line_y))

        if font_small and self.fade_in > 0.2:
            sub_a = int(alpha * min(1.0, (self.fade_in - 0.2) * 2))
            sub = clamp_surf(font_small.render("A TALE OF THE ANCIENT PROPHECY", True, (140, 110, 220)), sw - 20)
            sub.set_alpha(sub_a)
            screen.blit(sub, (cx - sub.get_width() // 2, subtitle_y))

        if font_large:
            for text, color, y in [
                ("SUPER ANIMAL",     (255, 220, 60), title_y - line_gap // 2),
                ("FIGHTING EXPLORER",(255, 180, 40), title_y + line_gap // 2),
            ]:
                surf = clamp_surf(font_large.render(text, True, color),   sw - 20)
                shd  = clamp_surf(font_large.render(text, True, (0,0,0)), sw - 20)
                surf.set_alpha(alpha)
                shd.set_alpha(alpha // 2)
                x = cx - surf.get_width() // 2
                screen.blit(shd,  (x + 2, y + 2))
                screen.blit(surf, (x, y))

        if self.fade_in > 0.5:
            line_a = int(180 * min(1.0, (self.fade_in - 0.5) * 2))
            ls = pygame.Surface((int(sw * 0.6), 1), pygame.SRCALPHA)
            ls.fill((120, 100, 220, line_a))
            screen.blit(ls, (cx - ls.get_width() // 2, bot_line_y))

        if font_medium and self.fade_in > 0.6:
            credit_a = int(alpha * min(1.0, (self.fade_in - 0.6) * 2.5))
            cr = font_medium.render("By Femi", True, (180, 160, 255))
            cr.set_alpha(credit_a)
            screen.blit(cr, (cx - cr.get_width() // 2, credit_y))

        if self._ready and font_small and not self.leaving:
            pulse = abs(math.sin(self.timer * 0.04)) * 0.5 + 0.5
            hint = clamp_surf(font_small.render("Click or press any key to begin", True, (120, 100, 180)), sw - 20)
            hint.set_alpha(int(220 * pulse))
            screen.blit(hint, (cx - hint.get_width() // 2, int(sh * 0.88)))

        if self.fade_out > 0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, int(255 * self.fade_out)))
            screen.blit(ov, (0, 0))
