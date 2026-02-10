import random
import pygame


class Creature:
    """
    Core creature model.
    Stats are configured externally so we can reuse the class for player/enemy scaling.
    """

    def __init__(self, element, level=1):
        self.element = element
        self.level = level
        self.max_health = 1
        self.current_health = 1
        self.damage_min = 1
        self.damage_max = 1
        self.max_special_uses = 1
        self.special_uses = self.max_special_uses
        self.sprite = self._placeholder_sprite((128, 128))

    def configure_stats(self, base_hp, hp_per_level, base_dmg_min, base_dmg_max, dmg_per_level):
        self.max_health = base_hp + self.level * hp_per_level
        self.current_health = self.max_health
        self.damage_min = base_dmg_min + self.level * dmg_per_level
        self.damage_max = base_dmg_max + self.level * dmg_per_level

    def roll_damage(self):
        return random.randint(self.damage_min, self.damage_max)

    def roll_special_damage(self):
        # Stronger than a normal hit, but not a one-shot.
        base = self.roll_damage()
        return int(base * 1.35 + 6)

    def take_damage(self, amount):
        self.current_health -= amount

    def is_defeated(self):
        return self.current_health <= 0

    def level_up(self):
        self.level += 1

    def reset_after_battle(self):
        self.current_health = self.max_health
        self.special_uses = self.max_special_uses

    def load_sprite(self, path):
        """
        Loads the sprite from disk.
        If it fails, a placeholder is used instead of crashing.
        """
        try:
            self.sprite = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError) as exc:
            print(f"Warning: could not load sprite '{path}': {exc}")
            self.sprite = self._placeholder_sprite((128, 128))

    def _placeholder_sprite(self, size):
        surface = pygame.Surface(size)
        surface.fill((80, 80, 80))
        pygame.draw.rect(surface, (200, 60, 60), surface.get_rect(), 3)
        pygame.draw.line(surface, (200, 60, 60), (0, 0), size, 3)
        pygame.draw.line(surface, (200, 60, 60), (0, size[1]), (size[0], 0), 3)
        return surface
