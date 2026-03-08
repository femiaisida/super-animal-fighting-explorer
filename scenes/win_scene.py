import pygame
from core.scene_manager import Scene
import systems.save_system as save_system


class WinScene(Scene):
    def __init__(self, manager, assets=None, player_party=None,
                 player_character="hero", save_data=None,
                 is_boss_victory=False, is_random=False,
                 run_complete=False, gold_earned=0, origin="map",
                 xp_gained=0, levelled_up=False, new_level=1):
        super().__init__(manager)
        self.assets           = assets
        self.player_party     = player_party
        self.player_character = player_character
        self.save_data        = save_data or {}
        self.is_boss_victory  = is_boss_victory
        self.is_random        = is_random
        self.run_complete     = run_complete
        self.gold_earned      = gold_earned
        self.origin           = origin
        self.assets.stop_music()
        self.xp_gained        = xp_gained
        self.levelled_up      = levelled_up
        self.new_level        = new_level
        self.font_large  = assets.get_font("large")  if assets else None
        self.font_medium = assets.get_font("medium") if assets else None
        self.font_small  = assets.get_font("small")  if assets else None
        info = pygame.display.Info()
        self.sw, self.sh = info.current_w, info.current_h
        self.timer = 0

    def handle_event(self, event):
        if self.timer < 60: return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if self.run_complete:
                from scenes.summary_scene import SummaryScene
                self.manager.switch(SummaryScene(self.manager, self.assets, self.save_data))
            elif self.origin == "explore":
                from scenes.explore_scene import ExploreScene
                self.manager.switch(ExploreScene(
                    self.manager, self.assets,
                    player_party=self.player_party,
                    player_character=self.player_character,
                    save_data=self.save_data,
                ))
            else:
                from scenes.map_scene import MapScene
                self.manager.switch(MapScene(
                    self.manager, self.assets,
                    player_party=self.player_party,
                    player_character=self.player_character,
                    save_data=self.save_data,
                    skip_npc=False,
                ))

    def update(self, dt):
        self.timer += 1

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2

        if self.run_complete:
            screen.fill((10,10,40))
        elif self.is_boss_victory:
            screen.fill((40,20,0))
        elif self.is_random:
            screen.fill((20,30,20))
        else:
            screen.fill((0,50,0))

        ov = pygame.Surface((sw,sh), pygame.SRCALPHA)
        ov.fill((0,0,0,70)); screen.blit(ov,(0,0))

        if self.run_complete:
            title_text, tc = "ALL SEALS RESTORED!", (255,200,50)
        elif self.is_boss_victory:
            title_text, tc = "GUARDIAN DEFEATED!", (255,140,30)
        elif self.is_random:
            title_text, tc = "AMBUSH SURVIVED!", (180,255,180)
        else:
            title_text, tc = "VICTORY!", (120,255,120)

        if self.font_large:
            t  = self.font_large.render(title_text, True, tc)
            sh_t = self.font_large.render(title_text, True, (0,0,0))
            screen.blit(sh_t, (cx-t.get_width()//2+3, int(sh*0.25)+3))
            screen.blit(t,    (cx-t.get_width()//2,   int(sh*0.25)))

        if self.gold_earned and self.font_medium:
            gs = self.font_medium.render(f"+{self.gold_earned} gold", True, (255,200,50))
            screen.blit(gs, (cx - gs.get_width()//2, int(sh*0.38)))

        if self.font_small:
            xp_col = (100, 255, 180) if self.levelled_up else (140, 200, 160)
            xs = self.font_small.render(f"+{self.xp_gained} XP", True, xp_col)
            screen.blit(xs, (cx - xs.get_width()//2, int(sh*0.45)))
            if self.levelled_up:
                ll = self.font_small.render(f"LEVEL UP!  Lv.{self.new_level}", True, (80, 255, 200))
                screen.blit(ll, (cx - ll.get_width()//2, int(sh*0.50)))
                if self.save_data and self.save_data.get("pending_evolution"):
                    ev = self.font_small.render("EVOLUTION READY!", True, (255, 160, 40))
                    screen.blit(ev, (cx - ev.get_width()//2, int(sh*0.55)))

        # Story narration line for boss victories
        if self.is_boss_victory and self.font_small:
            from systems.story import get_map_narration
            boss_kills = self.save_data.get("run_stats", {}).get("boss_kills", 0)
            narr = get_map_narration(boss_kills)
            if narr:
                ns = self.font_small.render(narr[0], True, (180,160,220))
                screen.blit(ns, (cx - ns.get_width()//2, int(sh*0.46)))

        cleared = [b for b in self.save_data.get("cleared_biomes",[])
                   if not b.endswith("_normal") and not b.endswith("_boss")]
        if self.font_medium and cleared:
            cl = self.font_medium.render(f"Seals restored: {len(cleared)} / 4", True, (180,220,180))
            screen.blit(cl, (cx-cl.get_width()//2, int(sh*0.52)))

        if self.player_party and self.font_medium:
            for i, c in enumerate(self.player_party):
                hp_col  = (100,220,100) if c.health > c.max_health*0.5 else (220,180,50)
                hp_text = f"{c.name}  HP: {max(0,c.health)} / {c.max_health}"
                t = self.font_medium.render(hp_text, True, hp_col)
                screen.blit(t, (cx-t.get_width()//2, int(sh*0.60)+i*36))

        # Evolution hint
        if not self.save_data.get("evolved",False) and self.is_boss_victory and self.font_small:
            evo = self.font_small.render(
                "A new power stirs within you... [E] on the map to evolve!",
                True, (220,150,255))
            screen.blit(evo, (cx-evo.get_width()//2, int(sh*0.72)))

        if self.timer >= 60 and self.font_small:
            hint = "Press any key to view run summary" if self.run_complete \
                   else "Press any key to return to map"
            h = self.font_small.render(hint, True, (180,255,180))
            screen.blit(h, (cx-h.get_width()//2, int(sh*0.82)))