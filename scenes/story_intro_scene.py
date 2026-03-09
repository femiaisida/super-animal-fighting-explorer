import pygame
from core.scene_manager import Scene
from systems.story import STORY_INTRO_PAGES, CHARACTER_INTRO


class StoryIntroScene(Scene):
    def __init__(self, manager, assets, character, on_complete):
        super().__init__(manager)
        self.assets      = assets
        self.character   = character
        self.on_complete = on_complete

        self.sw = assets.screen_w
        self.sh = assets.screen_h

        self.pages = list(STORY_INTRO_PAGES)
        char_lines = CHARACTER_INTRO.get(character, [])
        if char_lines:
            self.pages.append({
                "title":  "Your Story Begins",
                "lines":  char_lines,
                "colour": (220, 220, 100),
            })

        self.page_index = 0
        self.timer      = 0
        self.fade_in    = 0.0
        self.anim_time  = 0.0
        self._music_started = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_BACKSPACE):
                if self.page_index > 0 and self.timer >= 20:
                    self.page_index -= 1
                    self.timer   = 0
                    self.fade_in = 0.0
                    self.assets.play_sound("story")
                return
            if self.timer >= 30:
                self.assets.play_sound("story")
                self._advance()

        if event.type == pygame.MOUSEBUTTONDOWN and self.timer >= 30:
            if event.button == 1:
                if event.pos[0] < self.sw // 2 and self.page_index > 0:
                    self.page_index -= 1
                    self.timer   = 0
                    self.fade_in = 0.0
                    self.assets.play_sound("story")
                else:
                    self.assets.play_sound("story")
                    self._advance()

    def _advance(self):
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            self.timer   = 0
            self.fade_in = 0.0
        else:
            self.assets.stop_music()
            self.on_complete()

    def update(self, dt):
        if not self._music_started:
            self._music_started = True
            self.assets.play_music("story")
        self.timer     += 1
        self.anim_time += dt
        self.fade_in    = min(1.0, self.fade_in + dt * 2.0)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        page   = self.pages[self.page_index]
        col    = page.get("colour", (200, 200, 200))
        lh     = int(sh / 54)   # base line height

        screen.fill((5, 5, 15))

        alpha_val = int(255 * self.fade_in)

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # ── Story container box ───────────────────────────────────────────
        box_w = int(sw * 0.76)
        box_h = int(sh * 0.76)
        box_x = cx - box_w // 2
        box_y = int(sh * 0.08)
        box_pad = int(box_w * 0.05)   # horizontal padding inside box

        # Background fill
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill((*col[:3], 10))
        box_surf.set_alpha(alpha_val)
        screen.blit(box_surf, (box_x, box_y))

        # Border
        if self.fade_in > 0.2:
            border_a = int(180 * min(1.0, (self.fade_in - 0.2) * 2))
            brd_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            pygame.draw.rect(brd_surf, (*col[:3], border_a), (0, 0, box_w, box_h), 2,
                             border_radius=6)
            screen.blit(brd_surf, (box_x, box_y))

        # Corner accents
        if self.fade_in > 0.4:
            acc_a  = int(220 * min(1.0, (self.fade_in - 0.4) * 2))
            acc_sz = 16
            for ax, ay, dx, dy in [
                (box_x,           box_y,           1, 1),
                (box_x+box_w-1,   box_y,          -1, 1),
                (box_x,           box_y+box_h-1,   1,-1),
                (box_x+box_w-1,   box_y+box_h-1,  -1,-1),
            ]:
                pygame.draw.line(screen, (*col[:3], acc_a),
                                 (ax, ay), (ax + dx*acc_sz, ay), 2)
                pygame.draw.line(screen, (*col[:3], acc_a),
                                 (ax, ay), (ax, ay + dy*acc_sz), 2)

        # ── Title — top 18% of box interior ──────────────────────────────
        title_y = box_y + int(box_h * 0.07)
        max_title_w = box_w - box_pad * 2

        if font_large:
            t     = font_large.render(page["title"], True, col)
            shade = font_large.render(page["title"], True, (0, 0, 0))
            # Scale down if title wider than box interior
            if t.get_width() > max_title_w:
                scale = max_title_w / t.get_width()
                t     = pygame.transform.scale(t, (int(t.get_width()*scale), int(t.get_height()*scale)))
                shade = pygame.transform.scale(shade, (t.get_width(), t.get_height()))
            t.set_alpha(alpha_val)
            shade.set_alpha(alpha_val // 2)
            tx = cx - t.get_width() // 2
            screen.blit(shade, (tx + 2, title_y + 2))
            screen.blit(t,     (tx,     title_y))
            title_bottom = title_y + t.get_height()
        else:
            title_bottom = title_y + lh * 2

        # ── Horizontal rule — sits lh below title bottom ──────────────────
        rule_y = title_bottom + int(lh * 1.2)
        if self.fade_in > 0.5:
            da = int(160 * min(1.0, (self.fade_in - 0.5) * 2))
            ds = pygame.Surface((int(box_w * 0.7), 2), pygame.SRCALPHA)
            ds.fill((*col[:3], da))
            screen.blit(ds, (cx - ds.get_width() // 2, rule_y))

        # ── Story lines — start lh*1.5 below rule, spaced lh*2.0 apart ───
        # Calculate how many lines fit: box_bottom - margin - rule_y - gap
        box_bottom   = box_y + box_h
        lines        = [l for l in page.get("lines", []) if l]   # skip blank separators
        blank_count  = len(page.get("lines", [])) - len(lines)
        content_top  = rule_y + int(lh * 2.0)
        content_h    = box_bottom - int(lh * 2) - content_top     # leave bottom margin
        n_lines      = max(1, len(lines) + blank_count)
        line_gap     = min(int(lh * 2.2), content_h // n_lines) if n_lines else int(lh * 2.2)
        max_line_w   = box_w - box_pad * 2

        if font_medium:
            ly = content_top
            for i, line in enumerate(page.get("lines", [])):
                if not line:
                    ly += line_gap // 2
                    continue
                da   = max(0, min(255, int(255 * (self.fade_in - i * 0.08) * 3)))
                # Scale line to fit inside box
                surf = font_medium.render(line, True, (220, 220, 220))
                shd  = font_medium.render(line, True, (0, 0, 0))
                if surf.get_width() > max_line_w:
                    scale = max_line_w / surf.get_width()
                    surf = pygame.transform.scale(surf, (int(surf.get_width()*scale), int(surf.get_height()*scale)))
                    shd  = pygame.transform.scale(shd,  (surf.get_width(), surf.get_height()))
                surf.set_alpha(da)
                shd.set_alpha(da // 2)
                lx = cx - surf.get_width() // 2
                screen.blit(shd,  (lx + 1, ly + 1))
                screen.blit(surf, (lx,     ly))
                ly += line_gap

        # ── Page dots ────────────────────────────────────────────────────
        dot_y = int(sh * 0.88)
        n     = len(self.pages)
        dw, dg = 10, 6
        total  = n * dw + (n - 1) * dg
        dx     = cx - total // 2
        for i in range(n):
            c = col if i == self.page_index else (55, 55, 75)
            pygame.draw.circle(screen, c, (dx + i * (dw + dg) + dw // 2, dot_y), dw // 2)

        # ── Nav hints ─────────────────────────────────────────────────────
        if self.timer > 30 and font_small:
            last  = (self.page_index == len(self.pages) - 1)
            fwd   = "Any key to begin your journey" if last else "Any key / click to continue"
            fwd_s = self.assets.render_fitted("small", fwd, (100, 100, 120), sw - 40)
            if fwd_s:
                screen.blit(fwd_s, (cx - fwd_s.get_width() // 2, int(sh * 0.928)))

            if self.page_index > 0:
                back_s = self.assets.render_fitted("small", "← / Backspace to go back",
                                                   (80, 80, 100), sw - 40)
                if back_s:
                    screen.blit(back_s, (cx - back_s.get_width() // 2, int(sh * 0.960)))