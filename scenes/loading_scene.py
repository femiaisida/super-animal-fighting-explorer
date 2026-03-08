import pygame
import math
from core.scene_manager import Scene


class LoadingScene(Scene):
    """
    Opening splash screen. Shows game title and author credit.
    Auto-advances to CharacterSelectScene after ~3 seconds,
    or immediately on any key/click.
    """

    AUTO_ADVANCE_FRAMES = 200   # ~3.3 seconds at 60fps

    def __init__(self, manager, assets):
        super().__init__(manager)
        self.assets    = assets
        info           = pygame.display.Info()
        self.sw        = info.current_w
        self.sh        = info.current_h
        self.timer     = 0
        self.fade_in   = 0.0
        self.fade_out  = 0.0
        self.leaving   = False
        self._music_started = False

    def handle_event(self, event):
        if self.timer < 40:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._start_leave()

    def _start_leave(self):
        if not self.leaving:
            self.leaving = True
            self.assets.play_sound("click")

    def _go(self):
        from scenes.character_select_scene import CharacterSelectScene
        self._music_started = False
        self.manager.switch(CharacterSelectScene(self.manager, self.assets))

    def update(self, dt):
        if not self._music_started:
            self._music_started = True
            self.assets.play_music("menu")
        self.timer  += 1
        self.fade_in = min(1.0, self.fade_in + dt * 1.2)

        if self.timer >= self.AUTO_ADVANCE_FRAMES:
            self._start_leave()

        if self.leaving:
            self.fade_out = min(1.0, self.fade_out + dt * 3.0)
            if self.fade_out >= 1.0:
                self._go()

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx, cy = sw // 2, sh // 2

        screen.fill((4, 4, 14))

        # Animated star field
        for i in range(120):
            bx  = int((math.sin(i * 137.508) * 0.5 + 0.5) * sw)
            by  = int((math.cos(i * 137.508) * 0.5 + 0.5) * sh)
            twinkle = abs(math.sin(self.timer * 0.03 + i)) * 0.6 + 0.4
            a   = int(80 * twinkle * self.fade_in)
            if a > 0:
                s = pygame.Surface((3, 3), pygame.SRCALPHA)
                pygame.draw.circle(s, (180, 180, 255, a), (1, 1), 1)
                screen.blit(s, (bx, by))

        alpha = int(255 * self.fade_in)

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # Decorative top line
        if self.fade_in > 0.3:
            line_a = int(180 * min(1.0, (self.fade_in - 0.3) * 2))
            ls = pygame.Surface((int(sw * 0.5), 1), pygame.SRCALPHA)
            ls.fill((120, 100, 220, line_a))
            screen.blit(ls, (cx - ls.get_width() // 2, cy - 80))

        # Subtitle line above title
        if font_small and self.fade_in > 0.2:
            sub_a = int(alpha * min(1.0, (self.fade_in - 0.2) * 2))
            sub   = font_small.render("A TALE OF THE ANCIENT PROPHECY", True, (140, 110, 220))
            sub.set_alpha(sub_a)
            screen.blit(sub, (cx - sub.get_width() // 2, cy - 60))

        # Main title — two lines
        if font_large:
            line1 = font_large.render("SUPER ANIMAL", True, (255, 220, 60))
            line2 = font_large.render("FIGHTING EXPLORER", True, (255, 180, 40))
            sh1   = font_large.render("SUPER ANIMAL", True, (0, 0, 0))
            sh2   = font_large.render("FIGHTING EXPLORER", True, (0, 0, 0))
            for surf, shd, y in [
                (line1, sh1, cy - 18),
                (line2, sh2, cy + 16),
            ]:
                surf.set_alpha(alpha)
                shd.set_alpha(alpha // 2)
                x = cx - surf.get_width() // 2
                screen.blit(shd,  (x + 3, y + 3))
                screen.blit(surf, (x, y))

        # Decorative bottom line
        if self.fade_in > 0.5:
            line_a = int(180 * min(1.0, (self.fade_in - 0.5) * 2))
            ls = pygame.Surface((int(sw * 0.5), 1), pygame.SRCALPHA)
            ls.fill((120, 100, 220, line_a))
            screen.blit(ls, (cx - ls.get_width() // 2, cy + 52))

        # "By Femi" credit
        if font_medium and self.fade_in > 0.6:
            credit_a = int(alpha * min(1.0, (self.fade_in - 0.6) * 2.5))
            cr       = font_medium.render("By Femi", True, (180, 160, 255))
            cr.set_alpha(credit_a)
            screen.blit(cr, (cx - cr.get_width() // 2, cy + 76))

        # Press any key hint (pulsing)
        if self.timer > 60 and font_small and not self.leaving:
            pulse = abs(math.sin(self.timer * 0.04)) * 0.5 + 0.5
            hint  = font_small.render("Press any key to begin", True, (120, 100, 180))
            hint.set_alpha(int(200 * pulse))
            screen.blit(hint, (cx - hint.get_width() // 2, int(sh * 0.88)))

        # Fade-out overlay
        if self.fade_out > 0:
            ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
            ov.fill((0, 0, 0, int(255 * self.fade_out)))
            screen.blit(ov, (0, 0))