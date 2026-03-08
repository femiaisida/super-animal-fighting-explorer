"""
CombatSystem: Thin utility layer for combat calculations.
Core battle logic lives in BattleController — use this for
standalone damage calculations outside of a full battle context.
"""


class CombatSystem:
    def calculate_damage(self, attacker, defender, ability):
        """Calculate raw damage using ability, attacker, and defender stats."""
        return ability.calculate_damage(attacker, defender)

    def apply_ability(self, attacker, defender, ability):
        """
        Apply an ability directly (no event emission, no cooldown tracking).
        Use BattleController.perform_ability() for full battle logic.
        Returns damage dealt.
        """
        if not ability.is_ready():
            return 0

        damage = self.calculate_damage(attacker, defender, ability)
        defender.take_damage(damage)

        if ability.status_effect:
            defender.apply_status(ability.status_effect)

        ability.trigger_cooldown()
        return damage