class Creature:
    def __init__(self, name, max_health, abilities=None, image_path=None, position=None, element=None):
        self.name = name
        self.max_health = max_health
        self.health = max_health

        self.element = element
        self.abilities = abilities if abilities else []

        self.image_path = image_path
        self.position = position

        self.status_effects = []
        self.alive = True

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health:
            self.health = self.max_health

    def apply_status(self, status_effect):
        """Apply a copy of a status effect."""
        status_effect_copy = status_effect.copy()
        status_effect_copy.apply(self)

    def update_status_effects(self):
        """Update all status effects — called each turn."""
        for effect in self.status_effects[:]:
            effect.update(self)

    def is_alive(self):
        return self.alive