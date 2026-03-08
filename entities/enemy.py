from entities.creature import Creature


class Enemy(Creature):
    def __init__(self, name, max_health, abilities=None, image_path=None, position=None, element=None, ai=None, battle_tier=1):
        super().__init__(
            name=name,
            max_health=max_health,
            abilities=abilities,
            image_path=image_path,
            position=position,
            element=element
        )
        self.ai = ai
        self.battle_tier = battle_tier  # 1=normal 2=mid 3=elite

    def choose_action(self, player_party):
        """Use AI to choose ability and target."""
        if self.ai:
            return self.ai.choose_action(self, player_party)
        # Default: first ready ability, first living target
        for ability in self.abilities:
            if ability.is_ready():
                alive_targets = [p for p in player_party if p.is_alive()]
                if alive_targets:
                    return ability, alive_targets[0]
        return None, None