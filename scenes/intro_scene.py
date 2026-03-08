import pygame
from core.scene_manager import Scene


class IntroScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.Font(None, 48)

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill((50, 50, 100))
        text = self.font.render("Intro Scene", True, (255, 255, 255))
        screen.blit(text, (250, 250))