import pygame
from core.scene_manager import Scene
import systems.save_system as save_system


class LoseScene(Scene):
    def __init__(self, manager, assets=None, save_data=None, origin="map"):
        super().__init__(manager)
        self.assets      = assets
        self.save_data   = save_data or {}
        self.font_large  = assets.get_font("large")  if assets else None
        self.font_small  = assets.get_font("small")  if assets else None
        info             = pygame.display.Info()
        self.sw, self.sh = info.current_w, info.current_h
        self.timer       = 0
        if assets:
            assets.stop_music()

    def handle_event(self, event):
        if self.timer < 60: return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                from scenes.summary_scene import SummaryScene
                self.manager.switch(SummaryScene(self.manager, self.assets, self.save_data))
                return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            save_system.delete()
            from scenes.character_select_scene import CharacterSelectScene
            self.manager.switch(CharacterSelectScene(self.manager, self.assets))

    def update(self, dt):
        self.timer += 1

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw // 2
        screen.fill((50,0,0))
        ov = pygame.Surface((sw,sh),pygame.SRCALPHA); ov.fill((0,0,0,100)); screen.blit(ov,(0,0))

        if self.font_large:
            t  = self.font_large.render("DEFEATED!", True, (255,60,60))
            sh_t = self.font_large.render("DEFEATED!", True, (0,0,0))
            screen.blit(sh_t,(cx-t.get_width()//2+3,int(sh*0.30)+3))
            screen.blit(t,   (cx-t.get_width()//2,   int(sh*0.30)))

        if self.font_small:
            from systems.story import STORY_INTRO_PAGES
            qs = self.font_small.render(
                "\"The prophecy does not end here. It only rests.\"",
                True, (160,120,200))
            screen.blit(qs, (cx-qs.get_width()//2, int(sh*0.48)))

        if self.timer >= 60 and self.font_small:
            for i, line in enumerate(["[R]  View run summary", "[Any key]  New game"]):
                s = self.font_small.render(line, True, (220,160,160))
                screen.blit(s, (cx-s.get_width()//2, int(sh*0.62)+i*28))