"""
NPC Interaction Scene — full-screen dialogue with the NPC.
NPCs have a small chance to offer a gift (potion, gold, or elixir).
Player can read all dialogue lines and respond.
"""
import pygame
import random
import math
from core.scene_manager import Scene
import systems.save_system as save_system

# Gift pool: (item_key, display_name, probability_weight)
GIFT_POOL = [
    ("potion",  "Healing Potion", 50),
    ("gold_15", "15 Gold",        30),
    ("gold_30", "30 Gold",        15),
    ("elixir",  "Full Elixir",     5),
]
GIFT_CHANCE = 0.25   # 25% chance an NPC has a gift


class NPCScene(Scene):
    def __init__(self, manager, assets, npc_name, npc_lines, npc_sprite_key,
                 save_data, on_close):
        super().__init__(manager)
        self.assets         = assets
        self.npc_name       = npc_name
        self.npc_lines      = npc_lines   # list of dialogue strings
        self.npc_sprite_key = npc_sprite_key
        self.save_data      = save_data
        self.on_close       = on_close

        self.sw = assets.screen_w
        self.sh = assets.screen_h

        self.line_index  = 0
        self.timer       = 0
        self.fade_in     = 0.0
        self.anim_time   = 0.0
        self.assets.play_music("menu")

        # Gift logic
        self.has_gift     = random.random() < GIFT_CHANCE
        self.gift         = self._roll_gift() if self.has_gift else None
        self.gift_offered = False
        self.gift_taken   = False
        self.gift_msg     = ""
        self.gift_timer   = 0

        # Type-writer effect
        self.typed_chars  = 0.0
        self.type_speed   = 40.0   # chars per second

    def _roll_gift(self):
        weights = [g[2] for g in GIFT_POOL]
        total   = sum(weights)
        r       = random.uniform(0, total)
        acc     = 0
        for item in GIFT_POOL:
            acc += item[2]
            if r <= acc:
                return item
        return GIFT_POOL[0]

    @property
    def current_line(self):
        if self.line_index < len(self.npc_lines):
            return self.npc_lines[self.line_index]
        return ""

    @property
    def on_last_line(self):
        return self.line_index >= len(self.npc_lines) - 1

    @property
    def all_lines_done(self):
        return self.line_index >= len(self.npc_lines)

    def escape_quits(self):
        return False  # ESC closes NPC, doesn't quit game

    def handle_event(self, event):
        if self.timer < 20:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT):
                self._advance()
            elif event.key == pygame.K_g and self.gift_offered and not self.gift_taken:
                self._take_gift()
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
                self.on_close()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.gift_offered and not self.gift_taken:
                gr = self._gift_rect()
                dr = self._decline_rect()
                if gr.collidepoint(event.pos):
                    self._take_gift()
                    return
                if dr.collidepoint(event.pos):
                    self.on_close()
                    return
            next_r  = self._next_rect()
            close_r = self._close_rect()
            if next_r.collidepoint(event.pos):
                self._advance()
            elif close_r.collidepoint(event.pos):
                self.on_close()

    def _advance(self):
        # If typewriter not done, skip to full line first
        full_line = self.current_line
        if int(self.typed_chars) < len(full_line):
            self.typed_chars = float(len(full_line))
            self.assets.play_sound("click")
            return

        self.assets.play_sound("click")

        if self.on_last_line:
            # Check for gift after last line
            if self.has_gift and not self.gift_offered:
                self.gift_offered = True
                self.line_index += 1
            else:
                self.on_close()
        else:
            self.line_index  += 1
            self.typed_chars  = 0.0
            self.timer        = 0

    def _take_gift(self):
        if not self.gift or self.gift_taken:
            return
        self.gift_taken = True
        key = self.gift[0]
        if key == "potion":
            save_system.add_potion(self.save_data)
            self.gift_msg = "Received: Healing Potion!"
        elif key == "gold_15":
            save_system.add_gold(self.save_data, 15)
            self.gift_msg = "Received: 15 Gold!"
        elif key == "gold_30":
            save_system.add_gold(self.save_data, 30)
            self.gift_msg = "Received: 30 Gold!"
        elif key == "elixir":
            self.save_data["elixirs"] = self.save_data.get("elixirs", 0) + 1
            self.gift_msg = "Received: Full Elixir!"
        save_system.save(self.save_data)
        self.assets.play_sound("victory")
        self.gift_timer = 180

    def _gift_rect(self):
        w, h = int(self.sw * 0.22), int(self.sh * 0.07)
        cx   = self.sw // 2
        return pygame.Rect(cx - w - 20, int(self.sh * 0.72), w, h)

    def _decline_rect(self):
        w, h = int(self.sw * 0.22), int(self.sh * 0.07)
        cx   = self.sw // 2
        return pygame.Rect(cx + 20, int(self.sh * 0.72), w, h)

    def _next_rect(self):
        w, h = int(self.sw * 0.18), int(self.sh * 0.06)
        return pygame.Rect(self.sw - w - 40, int(self.sh * 0.76), w, h)

    def _close_rect(self):
        w, h = int(self.sw * 0.14), int(self.sh * 0.06)
        return pygame.Rect(self.sw - w - 40, int(self.sh * 0.84), w, h)

    def update(self, dt):
        self.timer     += 1
        self.anim_time += dt
        self.fade_in    = min(1.0, self.fade_in + dt * 2.5)
        if self.gift_timer > 0:
            self.gift_timer -= 1

        # Typewriter advance
        if not self.all_lines_done and not self.gift_offered:
            full = self.current_line
            if self.typed_chars < len(full):
                self.typed_chars = min(float(len(full)),
                                       self.typed_chars + self.type_speed * dt)

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2

        screen.fill((6, 8, 20))
        # Background glow
        glow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (80, 50, 160, 18),
                            (cx - sw // 3, sh // 2 - sh // 3, sw * 2 // 3, sh * 2 // 3))
        screen.blit(glow, (0, 0))

        alpha = int(255 * self.fade_in)
        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # ── Large NPC portrait left panel ────────────────────────────────
        portrait_x  = int(sw * 0.06)
        portrait_y  = int(sh * 0.15)
        portrait_sz = int(sh * 0.55)

        sprite = self.assets.get_image(self.npc_sprite_key) if self.npc_sprite_key else None
        if sprite:
            big = pygame.transform.scale(sprite, (portrait_sz, portrait_sz))
            # Subtle bob
            bob = int(math.sin(self.anim_time * 1.8) * 5)
            big.set_alpha(alpha)
            screen.blit(big, (portrait_x, portrait_y + bob))
            # Name plate under portrait
            if font_medium:
                np_surf  = font_medium.render(self.npc_name, True, (200, 160, 255))
                np_shade = font_medium.render(self.npc_name, True, (0, 0, 0))
                np_surf.set_alpha(alpha)
                np_shade.set_alpha(alpha // 2)
                nx = portrait_x + portrait_sz // 2 - np_surf.get_width() // 2
                ny = portrait_y + portrait_sz + bob + 12
                screen.blit(np_shade, (nx + 2, ny + 2))
                screen.blit(np_surf,  (nx, ny))
        else:
            # Placeholder box
            ph_r = pygame.Rect(portrait_x, portrait_y, portrait_sz, portrait_sz)
            pygame.draw.rect(screen, (40, 30, 70), ph_r, border_radius=12)
            pygame.draw.rect(screen, (100, 70, 160), ph_r, 2, border_radius=12)
            if font_medium:
                ns = font_medium.render(self.npc_name, True, (180, 140, 255))
                screen.blit(ns, (portrait_x + portrait_sz // 2 - ns.get_width() // 2,
                                 portrait_y + portrait_sz // 2))

        # ── Dialogue box (right side) ─────────────────────────────────────
        box_x  = portrait_x + portrait_sz + int(sw * 0.04)
        box_y  = int(sh * 0.15)
        box_w  = sw - box_x - int(sw * 0.06)
        box_h  = int(sh * 0.52)

        dbox = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        dbox.fill((14, 18, 40, 220))
        screen.blit(dbox, (box_x, box_y))
        pygame.draw.rect(screen, (95, 70, 155), (box_x, box_y, box_w, box_h), 2, border_radius=10)

        if not self.gift_offered:
            # Line counter dots
            total_lines = len(self.npc_lines)
            dw, dg = 8, 5
            total_dot_w = total_lines * dw + (total_lines - 1) * dg
            dot_start = box_x + box_w // 2 - total_dot_w // 2
            for di in range(total_lines):
                dc = (180, 140, 255) if di == self.line_index else (50, 40, 80)
                pygame.draw.circle(screen, dc,
                                   (dot_start + di * (dw + dg) + dw // 2, box_y + 18), dw // 2)

            # Dialogue text with typewriter
            if font_medium and not self.all_lines_done:
                shown = self.current_line[:int(self.typed_chars)]
                # Word-wrap manually
                words  = shown.split(" ")
                lines  = []
                cur    = ""
                max_w  = box_w - 40
                for word in words:
                    test = (cur + " " + word).strip()
                    if font_medium.size(test)[0] <= max_w:
                        cur = test
                    else:
                        if cur:
                            lines.append(cur)
                        cur = word
                if cur:
                    lines.append(cur)

                ty = box_y + 36
                for li, ln in enumerate(lines):
                    ls  = font_medium.render(ln, True, (225, 225, 230))
                    lsh = font_medium.render(ln, True, (0, 0, 0))
                    ls.set_alpha(alpha)
                    lsh.set_alpha(alpha // 2)
                    screen.blit(lsh, (box_x + 21, ty + 1))
                    screen.blit(ls,  (box_x + 20, ty))
                    ty += int(font_medium.get_height() * 1.5)

            # Blinking cursor
            if (self.timer // 20) % 2 == 0 and font_medium and not self.all_lines_done:
                cur_s = font_medium.render("▌", True, (180, 140, 255))
                screen.blit(cur_s, (box_x + 20, box_y + box_h - 30))

            # Advance hint
            if font_small and self.timer > 30:
                full = self.current_line if not self.all_lines_done else ""
                typed_done = int(self.typed_chars) >= len(full)
                if typed_done:
                    hint_txt = "ENTER to finish" if self.on_last_line else "ENTER for next"
                else:
                    hint_txt = "ENTER to skip"
                hs = font_small.render(hint_txt, True, (100, 80, 160))
                nr = self._next_rect()
                screen.blit(hs, (nr.x + nr.w // 2 - hs.get_width() // 2,
                                  nr.y + nr.h // 2 - hs.get_height() // 2))

        else:
            # ── Gift offer screen ─────────────────────────────────────────
            if not self.gift_taken:
                gift_name = self.gift[1] if self.gift else "?"
                offer_lines = [
                    "Wait — before you go.",
                    f"I have something for you.",
                    f"Take this: {gift_name}.",
                ]
                if font_medium:
                    ty = box_y + 36
                    for ln in offer_lines:
                        ls = font_medium.render(ln, True, (230, 210, 255))
                        screen.blit(ls, (box_x + 20, ty))
                        ty += int(font_medium.get_height() * 1.6)

                # Accept / Decline buttons
                gr = self._gift_rect()
                dr = self._decline_rect()
                pygame.draw.rect(screen, (35, 80, 35), gr, border_radius=8)
                pygame.draw.rect(screen, (80, 200, 80), gr, 2, border_radius=8)
                pygame.draw.rect(screen, (70, 30, 30), dr, border_radius=8)
                pygame.draw.rect(screen, (160, 60, 60), dr, 2, border_radius=8)
                if font_small:
                    ga = font_small.render(f"[G] Accept", True, (160, 255, 160))
                    da = font_small.render(f"[X] Decline", True, (255, 130, 130))
                    screen.blit(ga, (gr.x + gr.w // 2 - ga.get_width() // 2,
                                     gr.y + gr.h // 2 - ga.get_height() // 2))
                    screen.blit(da, (dr.x + dr.w // 2 - da.get_width() // 2,
                                     dr.y + dr.h // 2 - da.get_height() // 2))
            else:
                # Gift received message
                if font_large:
                    gs = font_large.render(self.gift_msg, True, (255, 220, 80))
                    screen.blit(gs, (cx - gs.get_width() // 2, box_y + box_h // 2 - 20))
                if font_small and self.gift_timer < 120:
                    hs = font_small.render("ENTER to leave", True, (120, 100, 180))
                    screen.blit(hs, (cx - hs.get_width() // 2, box_y + box_h // 2 + 30))
                if self.gift_timer == 0:
                    self.on_close()

        # Close hint
        if font_small and not self.gift_offered:
            cr = self._close_rect()
            pygame.draw.rect(screen, (35, 20, 45), cr, border_radius=6)
            pygame.draw.rect(screen, (80, 55, 100), cr, 1, border_radius=6)
            cx_s = font_small.render("[ESC] Leave", True, (100, 80, 130))
            screen.blit(cx_s, (cr.x + cr.w // 2 - cx_s.get_width() // 2,
                                cr.y + cr.h // 2 - cx_s.get_height() // 2))