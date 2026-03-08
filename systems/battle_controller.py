from core.event_bus import EventBus
from systems.type_system import get_multiplier, get_matchup_text


class BattleController:
    def __init__(self, player_party, enemy_party, event_bus: EventBus):
        self.player_party  = player_party
        self.enemy_party   = enemy_party
        self.event_bus     = event_bus
        self.turn_queue    = self.player_party + self.enemy_party
        self.current_index = 0

        # Run-level stats tracked here
        self.damage_dealt   = 0
        self.turns_taken    = 0
        self.abilities_used = 0

    def current_actor(self):
        return self.turn_queue[self.current_index]

    def next_turn(self):
        total = len(self.turn_queue)
        for _ in range(total):
            self.current_index = (self.current_index + 1) % total
            creature = self.turn_queue[self.current_index]
            if creature.is_alive():
                for ability in creature.abilities:
                    ability.reduce_cooldown()
                return creature
        return None

    def perform_ability(self, user, ability, target):
        if not ability.is_ready():
            return False, 0, ""
        if target is user:
            return False, 0, ""   # never allow self-damage

        # Base damage with type multiplier
        # Void element bypasses type system — always 1.0x, never resisted or boosted
        ability_elem = getattr(ability, "element", None) or getattr(user, "element", None)
        base_damage  = ability.calculate_damage(user, target)
        if ability_elem == "void" or getattr(user, "element", None) == "void":
            multiplier   = 1.0
            matchup_text, matchup_colour = "", (255, 255, 255)
        else:
            multiplier   = get_multiplier(ability_elem, getattr(target, "element", None))
            matchup_text, matchup_colour = get_matchup_text(
                ability_elem, getattr(target, "element", None)
            )
        damage = max(1, int(base_damage * multiplier))
        # Power boost: user's next hit is +50%
        if getattr(user, "power_boost", False):
            damage = int(damage * 1.5)
            user.power_boost = False
        # Shield: target's incoming damage is halved
        if getattr(target, "shield_active", False):
            damage = max(1, damage // 2)
            target.shield_active = False

        target.take_damage(damage)

        if ability.status_effect:
            from abilities.effects import Drain
            if isinstance(ability.status_effect, Drain):
                # Drain: heal the user instead of applying to target
                heal_amt = max(1, int(damage * ability.status_effect.fraction))
                user.heal(heal_amt)
            else:
                target.apply_status(ability.status_effect)

        ability.trigger_cooldown()

        # Track stats
        self.damage_dealt   += damage
        self.abilities_used += 1
        self.turns_taken    += 1

        self.event_bus.emit("ABILITY_USED", {
            "user":          user,
            "ability":       ability,
            "target":        target,
            "damage":        damage,
            "multiplier":    multiplier,
            "matchup_text":  matchup_text,
            "matchup_colour":matchup_colour,
        })

        return True, damage, matchup_text

    def update_status_effects(self):
        for creature in self.player_party + self.enemy_party:
            if creature.is_alive():
                creature.update_status_effects()

    def all_enemies_defeated(self):
        return all(not e.is_alive() for e in self.enemy_party)

    def all_players_defeated(self):
        return all(not p.is_alive() for p in self.player_party)