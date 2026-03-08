import pygame


class Ability:
    def __init__(self, name, power, status_effect=None, cooldown=0, icon_path=None, element=None):
        self.name = name
        self.power = power
        self.status_effect = status_effect
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.element = element   # "fire", "water", "nature", or None

        if icon_path:
            try:
                self.icon = pygame.image.load(icon_path).convert_alpha()
            except Exception as e:
                print(f"Error loading icon '{icon_path}': {e}")
                self.icon = None
        else:
            self.icon = None

    def is_ready(self):
        return self.current_cooldown == 0

    def trigger_cooldown(self):
        self.current_cooldown = self.cooldown

    def reduce_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def calculate_damage(self, user, target):
        return max(0, self.power + getattr(user, "attack", 0) - getattr(target, "defense", 0))