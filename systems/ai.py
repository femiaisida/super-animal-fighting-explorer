import random


class BasicAI:
    def choose_target(self, player_team):
        alive = [p for p in player_team if p.is_alive()]
        return random.choice(alive) if alive else None

    def choose_target_safe(self, enemy, player_team):
        """Never returns the enemy itself as a target."""
        alive = [p for p in player_team if p.is_alive() and p is not enemy]
        return random.choice(alive) if alive else None

    def choose_ability(self, enemy):
        ready = [a for a in enemy.abilities if a.is_ready()]
        if ready:
            return random.choice(ready)
        return enemy.abilities[0] if enemy.abilities else None

    def choose_action(self, enemy, player_team):
        """Return (ability, target) tuple for the enemy's turn."""
        ability = self.choose_ability(enemy)
        target  = self.choose_target_safe(enemy, player_team)
        return ability, target