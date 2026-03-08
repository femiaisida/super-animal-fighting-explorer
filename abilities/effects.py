class StatusEffect:
    """Base class for all status effects. Duration is measured in turns, not real time."""

    def __init__(self, name, duration):
        self.name = name
        self.duration = duration  # turns remaining
        self.turns_remaining = duration

    def apply(self, target):
        """Called when the effect is first applied to a target."""
        self.turns_remaining = self.duration
        target.status_effects.append(self)

    def update(self, target):
        """Called each turn. Subclasses should override and call super()."""
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.expire(target)

    def expire(self, target):
        """Remove the effect from the target."""
        if self in target.status_effects:
            target.status_effects.remove(self)

    def copy(self):
        """Return a fresh instance of the same effect."""
        return self.__class__(self.duration)


class Burn(StatusEffect):
    """Burn effect: deals damage each turn for a fixed number of turns."""

    def __init__(self, damage_per_turn, duration):
        super().__init__("Burn", duration)
        self.damage_per_turn = damage_per_turn

    def update(self, target):
        """Apply burn damage, then decrement turn counter."""
        target.take_damage(self.damage_per_turn)
        print(f"{target.name} takes {self.damage_per_turn} burn damage! ({self.turns_remaining - 1} turns left)")
        super().update(target)  # handles turns_remaining decrement and expiry

    def copy(self):
        return Burn(self.damage_per_turn, self.duration)


class Drain(StatusEffect):
    """Drain effect: attached to an ability hit — heals the attacker for a % of damage dealt.
    Applied as a one-shot effect (duration=1) that fires immediately."""

    def __init__(self, fraction=0.25):
        super().__init__("Drain", 1)
        self.fraction = fraction   # portion of damage to heal back
        self.attacker = None       # set by battle_controller before apply

    def update(self, target):
        # Healing is handled in battle_controller when it detects Drain
        # This just expires immediately
        super().update(target)

    def copy(self):
        return Drain(self.fraction)


class VoidCorruption(StatusEffect):
    """Void Corruption DoT — deals damage each turn, cannot be cleansed."""

    def __init__(self, damage_per_turn, duration):
        super().__init__("VoidCorruption", duration)
        self.damage_per_turn = damage_per_turn

    def update(self, target):
        target.take_damage(self.damage_per_turn)
        print(f"{target.name} writhes in void corruption! ({self.turns_remaining - 1} turns left)")
        super().update(target)

    def copy(self):
        return VoidCorruption(self.damage_per_turn, self.duration)