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
        info               = pygame.display.Info()
        self.sw            = info.current_w
        self.sh            = info.current_h
        self.message       = ""
        self.message_timer = 0
        self.selected_item = 0
        self.assets.play_music("menu")

    def escape_quits(self):
        return False  # ESC leaves shop

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
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(event.pos):
                    if self.selected_item == i:
                        self._buy(SHOP_ITEMS[i]["key"])
                    else:
                        self.selected_item = i
            if self._leave_rect().collidepoint(event.pos):
                self._leave()

        if event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._item_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_item = i

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
        item_h  = int(self.sh * 0.32)
        gap     = int(self.sw * 0.02)
        total_w = n * item_w + (n - 1) * gap
        start_x = self.sw // 2 - total_w // 2
        item_y  = int(self.sh * 0.38)
        return [pygame.Rect(start_x + i * (item_w + gap), item_y, item_w, item_h)
                for i in range(n)]

    def _leave_rect(self):
        w, h = int(self.sw * 0.20), int(self.sh * 0.07)
        return pygame.Rect(self.sw // 2 - w // 2, int(self.sh * 0.80), w, h)

    def update(self, dt):
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2

        screen.fill((8, 10, 22))
        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        screen.blit(ov, (0, 0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        # Panel
        pw, ph = int(sw * 0.72), int(sh * 0.74)
        panel  = pygame.Rect(cx - pw // 2, sh // 2 - ph // 2, pw, ph)
        ps     = pygame.Surface((pw, ph), pygame.SRCALPHA)
        ps.fill((16, 20, 42, 235))
        screen.blit(ps, panel.topleft)
        pygame.draw.rect(screen, (90, 90, 155), panel, 2, border_radius=14)

        # Title
        if font_large:
            t  = font_large.render("TRAVELLING MERCHANT", True, (255, 200, 80))
            ts = font_large.render("TRAVELLING MERCHANT", True, (0, 0, 0))
            tx = cx - t.get_width() // 2
            screen.blit(ts, (tx + 2, panel.y + 22))
            screen.blit(t,  (tx,     panel.y + 20))

        if font_small:
            fl = font_small.render(
                '"Strange times bring strange goods. Choose wisely."',
                True, (170, 150, 110))
            screen.blit(fl, (cx - fl.get_width() // 2, panel.y + 60))

        # Gold display with icon
        gold      = self.save_data.get("gold", 0)
        gold_icon = self.assets.get_image("icon_gold")
        if font_medium:
            gt = font_medium.render(f"{gold}g", True, (255, 200, 50))
            gx = cx - gt.get_width() // 2 - (14 if gold_icon else 0)
            gy = panel.y + 88
            if gold_icon:
                screen.blit(gold_icon, (gx - 4, gy - 2))
                screen.blit(gt, (gx + 24, gy))
            else:
                screen.blit(gt, (gx, gy))

        # Item cards
        rects = self._item_rects()
        for i, (item, rect) in enumerate(zip(SHOP_ITEMS, rects)):
            sel       = (i == self.selected_item)
            affordable = can_afford(self.save_data, item["cost"])

            bg_a  = (35, 55, 35, 210) if (affordable and sel) else \
                    (25, 25, 55, 210) if affordable else (30, 18, 18, 210)
            brd   = (100, 220, 100) if (affordable and sel) else \
                    (80, 80, 150)   if affordable else (80, 40, 40)

            cs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            cs.fill(bg_a)
            screen.blit(cs, rect.topleft)
            pygame.draw.rect(screen, brd, rect, 2 if sel else 1, border_radius=10)

            # Icon — 64x64 centred in top area
            icon = self.assets.get_image(item["img_key"])
            icon_y = rect.y + 14
            if icon:
                icon64 = pygame.transform.scale(icon, (64, 64))
                screen.blit(icon64, (rect.x + rect.w // 2 - 32, icon_y))
            else:
                # Coloured placeholder square
                pcolours = {"potion": (80,200,100), "elixir": (200,80,200),
                            "shield": (80,120,220), "power": (220,160,40)}
                pc = pcolours.get(item["key"], (120, 120, 120))
                pygame.draw.rect(screen, pc,
                                 (rect.x + rect.w//2 - 28, icon_y + 8, 56, 56),
                                 border_radius=8)

            ty = icon_y + 76
            if font_small:
                tc = (255, 255, 255) if affordable else (100, 100, 100)
                ns = font_small.render(item["name"], True, tc)
                screen.blit(ns, (rect.x + rect.w // 2 - ns.get_width() // 2, ty))

                dc = (150, 200, 150) if affordable else (75, 75, 75)
                ds = font_small.render(item["desc"], True, dc)
                screen.blit(ds, (rect.x + rect.w // 2 - ds.get_width() // 2, ty + 18))

                fc = (120, 110, 80) if affordable else (60, 55, 45)
                fv = font_small.render(item["flavour"], True, fc)
                screen.blit(fv, (rect.x + 5, ty + 38))

                cost_c = (255, 200, 50) if affordable else (140, 80, 80)
                cs2    = font_small.render(f"{item['cost']}g", True, cost_c)
                screen.blit(cs2, (rect.x + rect.w // 2 - cs2.get_width() // 2, rect.bottom - 22))

            if sel and font_small:
                hc   = (120, 220, 120) if affordable else (160, 80, 80)
                hint = font_small.render("ENTER to buy" if affordable else "Can't afford", True, hc)
                screen.blit(hint, (rect.x + rect.w // 2 - hint.get_width() // 2, rect.bottom - 38))

        # ── Leave Shop button ─────────────────────────────────────────────
        lr = self._leave_rect()
        pygame.draw.rect(screen, (55, 28, 28), lr, border_radius=10)
        pygame.draw.rect(screen, (190, 75, 75), lr, 2, border_radius=10)
        if font_medium:
            lt = font_medium.render("LEAVE SHOP", True, (245, 155, 155))
            screen.blit(lt, (cx - lt.get_width() // 2, lr.y + lr.h // 2 - lt.get_height() // 2))
        if font_small:
            lh = font_small.render("[L]", True, (140, 80, 80))
            screen.blit(lh, (lr.right + 8, lr.y + lr.h // 2 - lh.get_height() // 2))

        # Message
        if self.message_timer > 0 and font_small:
            ok  = any(w in self.message.lower() for w in ("purchased","added","ready","have"))
            mc  = (100, 220, 100) if ok else (220, 80, 80)
            ms  = font_small.render(self.message, True, mc)
            screen.blit(ms, (cx - ms.get_width() // 2, int(sh * 0.88)))

        if font_small:
            nav = font_small.render("← → browse   ENTER buy   L leave shop", True, (80, 80, 110))
            screen.blit(nav, (cx - nav.get_width() // 2, int(sh * 0.96)))