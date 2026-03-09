import pygame
from core.scene_manager import Scene
from systems.economy import SHOP_ITEMS, buy_item, can_afford
import systems.save_system as save_system


class ShopScene(Scene):
    def __init__(self, manager, assets, save_data, on_close):
        super().__init__(manager)
        self.assets        = assets
        self.save_data     = save_data
        self.on_close      = on_close
        self.sw            = assets.screen_w
        self.sh            = assets.screen_h
        self.message       = ""
        self.message_timer = 0
        self.selected_item = 0
        self.assets.play_music("menu")

    def escape_quits(self):
        return False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_item = (self.selected_item - 1) % len(SHOP_ITEMS)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_item = (self.selected_item + 1) % len(SHOP_ITEMS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._buy(SHOP_ITEMS[self.selected_item]["key"])
            elif event.key in (pygame.K_l, pygame.K_ESCAPE):
                self._leave()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._touch_start_x = event.pos[0]
            self._touch_moved   = False
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(event.pos):
                    if self.selected_item == i:
                        self._buy(SHOP_ITEMS[i]["key"])
                    else:
                        self.selected_item = i
            if self._leave_rect().collidepoint(event.pos):
                self._leave()

        if event.type == pygame.MOUSEMOTION:
            if getattr(self, "_touch_start_x", None) is not None:
                dx = event.pos[0] - self._touch_start_x
                if abs(dx) > 30:
                    self._touch_moved = True
                    if dx < 0:
                        self.selected_item = (self.selected_item + 1) % len(SHOP_ITEMS)
                    else:
                        self.selected_item = (self.selected_item - 1) % len(SHOP_ITEMS)
                    self._touch_start_x = event.pos[0]
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_item = i

        if event.type == pygame.MOUSEBUTTONUP:
            self._touch_start_x = None
            self._touch_moved   = False

    def _leave(self):
        self.assets.play_sound("click")
        self.on_close()

    def _buy(self, item_key):
        success, msg = buy_item(self.save_data, item_key)
        if success:
            save_system.save(self.save_data)
            self.assets.play_sound("click")
        self.message       = msg
        self.message_timer = 150

    def _item_rects(self):
        n       = len(SHOP_ITEMS)
        item_w  = int(self.sw * 0.16)
        item_h  = int(self.sh * 0.38)   # taller cards so text has room
        gap     = int(self.sw * 0.02)
        total_w = n * item_w + (n - 1) * gap
        start_x = self.sw // 2 - total_w // 2
        item_y  = int(self.sh * 0.34)
        return [pygame.Rect(start_x + i * (item_w + gap), item_y, item_w, item_h)
                for i in range(n)]

    def _leave_rect(self):
        w, h = int(self.sw * 0.20), int(self.sh * 0.07)
        return pygame.Rect(self.sw // 2 - w // 2, int(self.sh * 0.82), w, h)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= 1

    def _wrap_text(self, font, text, max_w):
        """Word-wrap text into lines fitting max_w. Returns list of strings."""
        words  = text.split()
        lines  = []
        cur    = ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines or [text]

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        lh     = int(sh / 54)   # base line height

        screen.fill((8, 10, 22))
        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        screen.blit(ov, (0, 0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # Panel
        pw, ph = int(sw * 0.80), int(sh * 0.82)
        panel  = pygame.Rect(cx - pw // 2, sh // 2 - ph // 2, pw, ph)
        ps     = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ps.fill((16, 20, 42, 235))
        screen.blit(ps, panel.topleft)
        pygame.draw.rect(screen, (90, 90, 155), panel, 2, border_radius=14)

        # Title
        if font_large:
            t  = font_large.render("TRAVELLING MERCHANT", True, (255, 200, 80))
            ts = font_large.render("TRAVELLING MERCHANT", True, (0, 0, 0))
            if t.get_width() > pw - 20:
                sc = (pw - 20) / t.get_width()
                t  = pygame.transform.scale(t,  (int(t.get_width()*sc), int(t.get_height()*sc)))
                ts = pygame.transform.scale(ts, (t.get_width(), t.get_height()))
            tx = cx - t.get_width() // 2
            screen.blit(ts, (tx + 2, panel.y + int(lh * 1.4) + 2))
            screen.blit(t,  (tx,     panel.y + int(lh * 1.4)))

        flavour_y = panel.y + int(lh * 4.0)
        if font_small:
            fl = self.assets.render_fitted("small",
                '"Strange times bring strange goods. Choose wisely."',
                (170, 150, 110), pw - 20)
            if fl:
                screen.blit(fl, (cx - fl.get_width() // 2, flavour_y))

        # Gold
        gold      = self.save_data.get("gold", 0)
        gold_icon = self.assets.get_image("icon_gold")
        gold_y    = flavour_y + int(lh * 2.2)
        if font_medium:
            gt = font_medium.render(f"{gold}g", True, (255, 200, 50))
            gx = cx - gt.get_width() // 2 - (14 if gold_icon else 0)
            if gold_icon:
                screen.blit(gold_icon, (gx - 4, gold_y - 2))
                screen.blit(gt, (gx + 24, gold_y))
            else:
                screen.blit(gt, (gx, gold_y))

        # Item cards
        rects = self._item_rects()
        for i, (item, rect) in enumerate(zip(SHOP_ITEMS, rects)):
            sel        = (i == self.selected_item)
            affordable = can_afford(self.save_data, item["cost"])

            bg_a = (35, 55, 35, 210) if (affordable and sel) else \
                   (25, 25, 55, 210) if affordable else (30, 18, 18, 210)
            brd  = (100, 220, 100) if (affordable and sel) else \
                   (80, 80, 150)   if affordable else (80, 40, 40)

            cs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cs.fill(bg_a)
            screen.blit(cs, rect.topleft)
            pygame.draw.rect(screen, brd, rect, 2 if sel else 1, border_radius=10)

            # Icon — top 36% of card
            icon_area_h = int(rect.h * 0.36)
            icon = self.assets.get_image(item["img_key"])
            icon_sz = min(56, icon_area_h - 8)
            icon_y  = rect.y + (icon_area_h - icon_sz) // 2
            if icon:
                icon_s = pygame.transform.scale(icon, (icon_sz, icon_sz))
                screen.blit(icon_s, (rect.x + rect.w // 2 - icon_sz // 2, icon_y))
            else:
                pcolours = {"potion": (80,200,100), "elixir": (200,80,200),
                            "shield": (80,120,220), "power": (220,160,40)}
                pc = pcolours.get(item["key"], (120, 120, 120))
                pygame.draw.rect(screen, pc,
                                 (rect.x + rect.w//2 - icon_sz//2, icon_y, icon_sz, icon_sz),
                                 border_radius=8)

            # Text section: bottom 64% of card
            # Slots from text_top (lh apart):
            #   name      → 0
            #   desc line1 → lh*1.8
            #   desc line2 → lh*3.2  (if wraps)
            #   flavour   → lh*4.8  (or lh*3.2 if desc is 1 line)
            #   price     → bottom - lh*2.8
            #   hint      → bottom - lh*1.2
            text_top  = rect.y + int(rect.h * 0.38)
            inner_w   = rect.w - 12

            if font_small:
                tc = (255, 255, 255) if affordable else (100, 100, 100)
                ns = self.assets.render_fitted("small", item["name"], tc, inner_w)
                if ns:
                    screen.blit(ns, (rect.x + rect.w//2 - ns.get_width()//2, text_top))

                # Wrap description
                dc = (150, 200, 150) if affordable else (75, 75, 75)
                desc_lines = self._wrap_text(font_small, item["desc"], inner_w) if font_small else [item["desc"]]
                desc_y = text_top + int(lh * 1.9)
                for dl in desc_lines[:2]:   # max 2 lines
                    ds = font_small.render(dl, True, dc)
                    screen.blit(ds, (rect.x + rect.w//2 - ds.get_width()//2, desc_y))
                    desc_y += int(lh * 1.6)

                # Flavour — wrap too, max 2 lines
                fc = (120, 110, 80) if affordable else (60, 55, 45)
                flav_lines = self._wrap_text(font_small, item["flavour"], inner_w) if font_small else [item["flavour"]]
                flav_y = desc_y + int(lh * 0.4)
                for fl in flav_lines[:2]:
                    fv = font_small.render(fl, True, fc)
                    screen.blit(fv, (rect.x + 6, flav_y))
                    flav_y += int(lh * 1.5)

                # Price — pinned above bottom
                cost_c = (255, 200, 50) if affordable else (140, 80, 80)
                cs2    = font_small.render(f"{item['cost']}g", True, cost_c)
                screen.blit(cs2, (rect.x + rect.w//2 - cs2.get_width()//2,
                                   rect.bottom - int(lh * 2.8)))

            # Hint — pinned to very bottom
            if sel and font_small:
                hc   = (120, 220, 120) if affordable else (160, 80, 80)
                hint = self.assets.render_fitted("small",
                    "ENTER to buy" if affordable else "Can't afford", hc, inner_w)
                if hint:
                    screen.blit(hint, (rect.x + rect.w//2 - hint.get_width()//2,
                                       rect.bottom - int(lh * 1.2)))

        # Leave button
        lr = self._leave_rect()
        pygame.draw.rect(screen, (55, 28, 28), lr, border_radius=10)
        pygame.draw.rect(screen, (190, 75, 75), lr, 2, border_radius=10)
        if font_medium:
            lt = self.assets.render_fitted("medium", "LEAVE SHOP", (245, 155, 155), lr.w - 16)
            if lt:
                screen.blit(lt, (cx - lt.get_width() // 2, lr.y + lr.h//2 - lt.get_height()//2))
        if font_small:
            lh_s = font_small.render("[L]", True, (140, 80, 80))
            screen.blit(lh_s, (lr.right + 8, lr.y + lr.h//2 - lh_s.get_height()//2))

        # Message
        if self.message_timer > 0 and font_small:
            ok  = any(w in self.message.lower() for w in ("purchased","added","ready","have"))
            mc  = (100, 220, 100) if ok else (220, 80, 80)
            ms  = self.assets.render_fitted("small", self.message, mc, sw - 40)
            if ms:
                screen.blit(ms, (cx - ms.get_width() // 2, int(sh * 0.905)))

        if font_small:
            nav = self.assets.render_fitted("small",
                "← → browse   ENTER buy   L leave shop", (80, 80, 110), sw - 20)
            if nav:
                screen.blit(nav, (cx - nav.get_width() // 2, int(sh * 0.960)))