import pygame
from core.scene_manager import SceneManager
from core.asset_manager import AssetManager


class Game:
    def __init__(self, web_mode=False):
        pygame.init()
        if web_mode:
            self.width, self.height = 960, 540
            self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            info = pygame.display.Info()
            self.width  = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height),
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            )
        pygame.display.set_caption("Super Animal Fighting Explorer")

        self.clock   = pygame.time.Clock()
        self.running = True

        self.assets = AssetManager(self.width, self.height)
        self.assets.load_all()

        self.scene_manager = SceneManager(None)

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.scene_manager.handle_event(event)

            self.scene_manager.update(dt)
            self.scene_manager.draw(self.screen)
            pygame.display.flip()

        pygame.quit()