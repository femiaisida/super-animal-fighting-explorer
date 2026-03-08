import pygame
from core.scene_manager import Scene
from systems.story import BIOME_INTROS


class BiomeIntroScene(Scene):
    """Shown the first time a player enters a biome. One page, then battle."""

    def __init__(self, manager, assets, biome_key, on_complete):
        super().__init__(manager)
        self.assets      = assets
        self.biome_key   = biome_key
        self.on_complete = on_complete
        info    = pygame.display.Info()
        self.sw = info.current_w
        self.sh = info.current_h
        self.timer     = 0
        self.fade_in   = 0.0
        self.data      = BIOME_INTROS.get(biome_key, {
            "title": biome_key.title(),
            "lines": ["A new biome awaits.", "Prepare for battle."],
            "colour": (200, 200, 200),
        })

    def handle_event(self, event):
        if self.timer < 40:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.assets.play_sound("click")
            self.on_complete()

    def update(self, dt):
        self.timer   += 1
        self.fade_in  = min(1.0, self.fade_in + dt * 1.8)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        col    = self.data.get("colour", (200, 200, 200))

        # Biome background faded
        bg = self.assets.get_image(
            {"forest": "bg_forest", "lava": "bg_lava",
             "ocean": "bg_ocean", "ruins": "bg_ruins"}.get(self.biome_key, "battle_bg")
        )
        if bg:
            faded = bg.copy()
            faded.set_alpha(60)
            screen.blit(faded, (0, 0))
        else:
            screen.fill((10, 10, 20))

        # Dark overlay
        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        alpha_val = int(255 * self.fade_in)

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # Title
        if font_large:
            t  = font_large.render(self.data["title"], True, col)
            sh_t = font_large.render(self.data["title"], True, (0, 0, 0))
            t.set_alpha(alpha_val)
            sh_t.set_alpha(alpha_val // 2)
            tx = cx - t.get_width() // 2
            screen.blit(sh_t, (tx + 2, int(sh * 0.20) + 2))
            screen.blit(t,    (tx,     int(sh * 0.20)))

        # Divider
        if self.fade_in > 0.4:
            da = int(200 * min(1.0, (self.fade_in - 0.4) * 2))
            ds = pygame.Surface((int(sw * 0.45), 2), pygame.SRCALPHA)
            ds.fill((*col[:3], da))
            screen.blit(ds, (cx - ds.get_width() // 2, int(sh * 0.30)))

        # Lines
        if font_medium:
            ly  = int(sh * 0.36)
            gap = int(sh * 0.07)
            for i, line in enumerate(self.data["lines"]):
                da = max(0, min(255, int(255 * (self.fade_in - i * 0.1) * 2.5)))
                s  = font_medium.render(line, True, (210, 210, 210))
                sh_s = font_medium.render(line, True, (0, 0, 0))
                s.set_alpha(da)
                sh_s.set_alpha(da // 2)
                lx = cx - s.get_width() // 2
                screen.blit(sh_s, (lx + 1, ly + 1))
                screen.blit(s,    (lx,     ly))
                ly += gap

        if self.timer > 40 and font_small:
            h = font_small.render("Press any key to enter", True, (100, 100, 120))
            screen.blit(h, (cx - h.get_width() // 2, int(sh * 0.90)))