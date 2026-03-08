import pygame
class Scene:
    def __init__(self, manager):
        self.manager = manager

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

    def escape_quits(self):
        """Return False to block ESC-to-quit (e.g. modal scenes with their own ESC handler)."""
        return True


class SceneManager:
    def __init__(self, starting_scene):
        self.scene = starting_scene

    def switch(self, new_scene):
        self.scene = new_scene

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if not self.scene or self.scene.escape_quits():
                import pygame as _pg, sys
                _pg.quit()
                sys.exit()
        if self.scene:
            self.scene.handle_event(event)

    def update(self, dt):
        if self.scene:
            self.scene.update(dt)

    def draw(self, screen):
        if self.scene:
            self.scene.draw(screen)