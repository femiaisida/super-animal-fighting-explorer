"""
Ambush Scene — shown before a random encounter.
Dramatic warning with biome background, then launches battle.
"""
import pygame
import random
import math
from core.scene_manager import Scene

AMBUSH_LINES = [
    "Something moves in the shadows...",
    "You sense a presence nearby...",
    "The ground trembles beneath you...",
    "A creature blocks your path!",
    "You've been spotted!",
    "An enemy emerges from the dark...",
]


class AmbushScene(Scene):
    def __init__(self, manager, assets, bg_key, biome_name, on_complete):
        super().__init__(manager)
        self.assets     = assets
        self.bg_key     = bg_key
        self.biome_name = biome_name
        self.on_complete = on_complete

        info    = pygame.display.Info()
        self.sw = info.current_w
        self.sh = info.current_h

        self.timer     = 0
        self.fade_in   = 0.0
        self.fade_out  = 0.0
        self.leaving   = False
        self.line      = random.choice(AMBUSH_LINES)

        # Play boss sting sound for drama
        self.assets.play_sound("boss_sting")

    def handle_event(self, event):
        if self.timer < 40:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self._leave()

    def _leave(self):
        if not self.leaving:
            self.leaving = True

    def update(self, dt):
        self.timer  += 1
        self.fade_in = min(1.0, self.fade_in + dt * 2.5)

        # Auto-advance after 2.5 seconds
        if self.timer > 150:
            self._leave()

        if self.leaving:
            self.fade_out = min(1.0, self.fade_out + dt * 4.0)
            if self.fade_out >= 1.0:
                self.on_complete()

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx, cy = sw // 2, sh // 2

        # Biome background — dark
        bg = self.assets.get_image(self.bg_key)
        if bg:
            screen.blit(bg, (0, 0))
        else:
            screen.fill((10, 5, 15))

        # Heavy dark overlay
        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        screen.blit(ov, (0, 0))

        # Red pulse vignette
        pulse = abs(math.sin(self.timer * 0.08)) * 0.5 + 0.5
        for r in range(3):
            vg = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.rect(vg, (160, 20, 20, int(30 * pulse)),
                             (r * 8, r * 6, sw - r * 16, sh - r * 12), 6 + r * 4)
            screen.blit(vg, (0, 0))

        alpha = int(255 * self.fade_in)
        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # "AMBUSH!" title
        if font_large:
            shake_x = random.randint(-3, 3) if self.timer < 30 else 0
            shake_y = random.randint(-2, 2) if self.timer < 30 else 0
            t  = font_large.render("AMBUSH!", True, (255, 60, 60))
            ts = font_large.render("AMBUSH!", True, (0, 0, 0))
            t.set_alpha(alpha)
            ts.set_alpha(alpha // 2)
            tx = cx - t.get_width() // 2 + shake_x
            ty = int(sh * 0.32) + shake_y
            screen.blit(ts, (tx + 3, ty + 3))
            screen.blit(t,  (tx, ty))

        # Biome label
        if font_medium and self.fade_in > 0.3:
            a2 = int(alpha * min(1.0, (self.fade_in - 0.3) * 2))
            bl = font_medium.render(f"in the {self.biome_name}", True, (200, 160, 100))
            bl.set_alpha(a2)
            screen.blit(bl, (cx - bl.get_width() // 2, int(sh * 0.44)))

        # Flavour line
        if font_medium and self.fade_in > 0.5:
            a3 = int(alpha * min(1.0, (self.fade_in - 0.5) * 2))
            ll = font_medium.render(self.line, True, (220, 220, 220))
            ll.set_alpha(a3)
            screen.blit(ll, (cx - ll.get_width() // 2, int(sh * 0.56)))

        # Continue hint
        if self.timer > 60 and font_small:
            hp = abs(math.sin(self.timer * 0.06)) * 0.5 + 0.5
            hs = font_small.render("Press any key to fight!", True, (200, 100, 100))
            hs.set_alpha(int(200 * hp))
            screen.blit(hs, (cx - hs.get_width() // 2, int(sh * 0.88)))

        # Fade out
        if self.fade_out > 0:
            fo = pygame.Surface((sw, sh), pygame.SRCALPHA)
            fo.fill((0, 0, 0, int(255 * self.fade_out)))
            screen.blit(fo, (0, 0))