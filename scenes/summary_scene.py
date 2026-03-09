import pygame
import math
from core.scene_manager import Scene
import systems.save_system as save_system


class SummaryScene(Scene):
    def __init__(self, manager, assets, save_data):
        super().__init__(manager)
        self.assets    = assets
        self.save_data = save_data
        self.sw        = assets.screen_w
        self.sh        = assets.screen_h
        self.timer     = 0
        self.font_large  = assets.get_font("large")
        self.font_medium = assets.get_font("medium")
        self.font_small  = assets.get_font("small")

    def _explore_rect(self):
        w, h = int(self.sw * 0.28), int(self.sh * 0.07)
        return pygame.Rect(self.sw // 2 - w - 20, int(self.sh * 0.88), w, h)

    def _end_rect(self):
        w, h = int(self.sw * 0.28), int(self.sh * 0.07)
        return pygame.Rect(self.sw // 2 + 20, int(self.sh * 0.88), w, h)

    def handle_event(self, event):
        if self.timer < 90: return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._explore_rect().collidepoint(event.pos):
                self._go_explore()
                return
            if self._end_rect().collidepoint(event.pos):
                self._go_end()
                return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self._go_explore()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_q):
                self._go_end()

    def _go_explore(self):
        from scenes.explore_scene import ExploreScene
        self.manager.switch(ExploreScene(
            self.manager, self.assets,
            player_character=self.save_data.get("player_character", "void"),
            save_data=self.save_data,
        ))

    def _go_end(self):
        save_system.delete()
        from scenes.character_select_scene import CharacterSelectScene
        self.manager.switch(CharacterSelectScene(self.manager, self.assets))

    def update(self, dt):
        self.timer += 1

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        screen.fill((8,8,20))

        # Star field
        for i in range(80):
            bx = int((math.sin(i*137.5)*0.5+0.5)*sw)
            by = int((math.cos(i*137.5)*0.5+0.5)*sh)
            pygame.draw.circle(screen, (60,60,100), (bx,by), 1)

        ov = pygame.Surface((sw,sh),pygame.SRCALPHA); ov.fill((0,0,0,50)); screen.blit(ov,(0,0))

        if self.font_large:
            t  = self.font_large.render("RUN COMPLETE", True, (255,200,50))
            sh_t = self.font_large.render("RUN COMPLETE", True, (0,0,0))
            screen.blit(sh_t,(cx-t.get_width()//2+3,int(sh*0.06)+3))
            screen.blit(t,   (cx-t.get_width()//2,   int(sh*0.06)))

        # Closing story line
        if self.font_small:
            closing = self.font_small.render(
                "\"The seals hold. The Voidcorrupt sleeps. For now.\"",
                True, (180,150,220))
            screen.blit(closing, (cx-closing.get_width()//2, int(sh*0.17)))

        stats   = self.save_data.get("run_stats", {})
        char    = self.save_data.get("player_character","?").upper()
        evolved = self.save_data.get("evolved", False)
        cleared = [b for b in self.save_data.get("cleared_biomes",[])
                   if not b.endswith("_normal") and not b.endswith("_boss")]

        if self.font_medium:
            evo_txt = " (Evolved)" if evolved else ""
            cs = self.font_medium.render(f"Champion: {char}{evo_txt}", True, (180,220,255))
            screen.blit(cs, (cx-cs.get_width()//2, int(sh*0.24)))

        stat_rows = [
            ("Seals Restored",  f"{len(cleared)} / 4",                (100,220,100)),
            ("Guardians Slain", str(stats.get("boss_kills",    0)),    (255,140, 30)),
            ("Total Damage",    str(stats.get("damage_dealt",  0)),    (255,100,100)),
            ("Gold Earned",     str(stats.get("gold_earned",   0))+"g",(255,200, 50)),
            ("Turns Taken",     str(stats.get("turns_taken",   0)),    (180,180,255)),
            ("Potions Used",    str(stats.get("potions_used",  0)),    (100,220,150)),
            ("Abilities Used",  str(stats.get("abilities_used",0)),    (220,200,100)),
        ]

        if self.font_medium:
            row_y   = int(sh*0.31)
            row_gap = int(sh*0.068)
            bar_w   = int(sw*0.40)
            bar_x   = cx - bar_w//2
            for label, value, col in stat_rows:
                ls = self.font_medium.render(label, True, (170,170,170))
                vs = self.font_medium.render(value, True, col)
                screen.blit(ls, (bar_x, row_y))
                screen.blit(vs, (bar_x + bar_w - vs.get_width(), row_y))
                pygame.draw.line(screen,(50,50,80),
                    (bar_x, row_y+ls.get_height()+3),
                    (bar_x+bar_w, row_y+ls.get_height()+3),1)
                row_y += row_gap

        if self.font_large:
            rt, rc = self._get_rating(stats, cleared, evolved)
            rs  = self.font_large.render(rt, True, rc)
            rsh = self.font_large.render(rt, True, (0,0,0))
            screen.blit(rsh,(cx-rs.get_width()//2+2,int(sh*0.82)+2))
            screen.blit(rs, (cx-rs.get_width()//2,   int(sh*0.82)))

        if self.timer >= 90 and self.font_small:
            # Explore button
            er = self._explore_rect()
            mx, my = pygame.mouse.get_pos()
            e_hov = er.collidepoint(mx, my)
            pygame.draw.rect(screen, (20,60,80) if e_hov else (15,40,55), er, border_radius=8)
            pygame.draw.rect(screen, (80,200,255) if e_hov else (50,120,160), er, 2, border_radius=8)
            et = self.font_small.render("[E] Keep Exploring", True, (100,220,255))
            screen.blit(et, (er.x + er.w//2 - et.get_width()//2, er.y + er.h//2 - et.get_height()//2))
            # End button
            qr = self._end_rect()
            q_hov = qr.collidepoint(mx, my)
            pygame.draw.rect(screen, (60,20,20) if q_hov else (40,15,15), qr, border_radius=8)
            pygame.draw.rect(screen, (255,100,80) if q_hov else (160,60,50), qr, 2, border_radius=8)
            qt = self.font_small.render("[ENTER] End Run", True, (255,140,120))
            screen.blit(qt, (qr.x + qr.w//2 - qt.get_width()//2, qr.y + qr.h//2 - qt.get_height()//2))

    def _get_rating(self, stats, cleared, evolved):
        bosses = stats.get("boss_kills",0)
        turns  = stats.get("turns_taken",0)
        if len(cleared)==4 and bosses==4 and evolved and turns<60:
            return "RATING: S+", (255,220,0)
        if len(cleared)==4 and bosses==4 and turns<60:
            return "RATING: S",  (255,200,0)
        if len(cleared)==4 and bosses>=3:
            return "RATING: A",  (180,100,255)
        if len(cleared)>=3:
            return "RATING: B",  (100,180,255)
        if len(cleared)>=2:
            return "RATING: C",  (100,220,100)
        return "RATING: D", (180,180,180)