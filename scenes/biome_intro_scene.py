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
        self.sw          = assets.screen_w
        self.sh          = assets.screen_h
        self.timer       = 0
        self.fade_in     = 0.0
        self.data        = BIOME_INTROS.get(biome_key, {
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
        sw, sh    = self.sw, self.sh
        cx        = sw // 2
        col       = self.data.get("colour", (200, 200, 200))
        lh        = int(sh / 54)
        alpha_val = int(255 * self.fade_in)

        # Background
        bg = self.assets.get_image(
            {"forest": "bg_forest", "lava": "bg_lava",
             "ocean": "bg_ocean",   "ruins": "bg_ruins"}.get(self.biome_key, "battle_bg")
        )
        if bg:
            faded = bg.copy()
            faded.set_alpha(60)
            screen.blit(faded, (0, 0))
        else:
            screen.fill((10, 10, 20))

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        screen.blit(ov, (0, 0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # ── Container box centred on screen ──────────────────────────────
        box_w = int(sw * 0.70)
        box_h = int(sh * 0.65)
        box_x = cx - box_w // 2
        box_y = int(sh * 0.15)

        box_s = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_s.fill((*col[:3], 8))
        box_s.set_alpha(alpha_val)
        screen.blit(box_s, (box_x, box_y))

        if self.fade_in > 0.2:
            ba = int(160 * min(1.0, (self.fade_in - 0.2) * 2))
            bs = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*col[:3], ba), (0, 0, box_w, box_h), 2, border_radius=6)
            screen.blit(bs, (box_x, box_y))

        # ── Title ─────────────────────────────────────────────────────────
        title_y   = box_y + int(box_h * 0.10)
        max_text_w = box_w - int(box_w * 0.10)

        if font_large:
            t    = font_large.render(self.data["title"], True, col)
            sh_t = font_large.render(self.data["title"], True, (0, 0, 0))
            if t.get_width() > max_text_w:
                sc   = max_text_w / t.get_width()
                t    = pygame.transform.scale(t,    (int(t.get_width()*sc),    int(t.get_height()*sc)))
                sh_t = pygame.transform.scale(sh_t, (t.get_width(), t.get_height()))
            t.set_alpha(alpha_val)
            sh_t.set_alpha(alpha_val // 2)
            tx = cx - t.get_width() // 2
            screen.blit(sh_t, (tx + 2, title_y + 2))
            screen.blit(t,    (tx,     title_y))
            title_bottom = title_y + t.get_height()
        else:
            title_bottom = title_y + lh * 2

        # ── Divider ───────────────────────────────────────────────────────
        divider_y = title_bottom + int(lh * 1.4)
        if self.fade_in > 0.4:
            da = int(200 * min(1.0, (self.fade_in - 0.4) * 2))
            ds = pygame.Surface((int(sw * 0.45), 2), pygame.SRCALPHA)
            ds.fill((*col[:3], da))
            screen.blit(ds, (cx - ds.get_width() // 2, divider_y))

        # ── Lines — evenly distributed below divider ──────────────────────
        lines       = self.data.get("lines", [])
        content_top = divider_y + int(lh * 2.0)
        box_bottom  = box_y + box_h - int(lh * 1.5)
        avail_h     = box_bottom - content_top
        n_lines     = len(lines) if lines else 1
        line_gap    = min(int(lh * 2.8), avail_h // n_lines)

        if font_medium:
            ly = content_top
            for i, line in enumerate(lines):
                da   = max(0, min(255, int(255 * (self.fade_in - i * 0.1) * 2.5)))
                s    = font_medium.render(line, True, (210, 210, 210))
                sh_s = font_medium.render(line, True, (0, 0, 0))
                # Scale if too wide
                if s.get_width() > max_text_w:
                    sc   = max_text_w / s.get_width()
                    s    = pygame.transform.scale(s,    (int(s.get_width()*sc),    int(s.get_height()*sc)))
                    sh_s = pygame.transform.scale(sh_s, (s.get_width(), s.get_height()))
                s.set_alpha(da)
                sh_s.set_alpha(da // 2)
                lx = cx - s.get_width() // 2
                screen.blit(sh_s, (lx + 1, ly + 1))
                screen.blit(s,    (lx,     ly))
                ly += line_gap

        if self.timer > 40 and font_small:
            h = self.assets.render_fitted("small", "Press any key to enter",
                                          (100, 100, 120), sw - 40)
            if h:
                screen.blit(h, (cx - h.get_width() // 2, int(sh * 0.88)))