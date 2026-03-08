"""
VFX system — handles:
  - Floating damage numbers
  - Ability hit flash (colour tint per element type)
  - Idle sprite bobbing animation
"""

import pygame
import math
import random


# ── Type colours for ability flashes ─────────────────────────────────────────

ABILITY_FLASH_COLOURS = {
    "fire":   (255, 120,  30),
    "water":  ( 40, 160, 255),
    "nature": ( 60, 200,  60),
    "boss":   (200,  60, 200),
    "default":(255, 255, 255),
}


# ── Floating damage number ────────────────────────────────────────────────────

class FloatingNumber:
    LIFETIME = 70   # frames

    def __init__(self, x, y, text, colour=(255, 60, 60), font=None):
        self.x      = float(x)
        self.y      = float(y)
        self.text   = text
        self.colour = colour
        self.font   = font
        self.age    = 0
        self.vx     = random.uniform(-0.6, 0.6)
        self.vy     = -2.2   # floats upward

    @property
    def alive(self):
        return self.age < self.LIFETIME

    def update(self):
        self.age += 1
        self.x   += self.vx
        self.y   += self.vy
        self.vy  *= 0.92   # decelerate

    def draw(self, screen):
        if not self.font:
            return
        alpha   = max(0, 255 - int(255 * (self.age / self.LIFETIME)))
        colour  = (*self.colour[:3], alpha)
        surf    = self.font.render(self.text, True, self.colour)
        surf.set_alpha(alpha)
        shadow  = self.font.render(self.text, True, (0, 0, 0))
        shadow.set_alpha(alpha // 2)
        screen.blit(shadow, (int(self.x) + 2, int(self.y) + 2))
        screen.blit(surf,   (int(self.x),     int(self.y)))


# ── Ability hit flash particle ────────────────────────────────────────────────

class HitFlash:
    LIFETIME = 18

    def __init__(self, x, y, colour=(255, 255, 255), size=60):
        self.x      = x
        self.y      = y
        self.colour = colour
        self.size   = size
        self.age    = 0

    @property
    def alive(self):
        return self.age < self.LIFETIME

    def update(self):
        self.age += 1

    def draw(self, screen):
        progress = self.age / self.LIFETIME
        radius   = int(self.size * (0.3 + progress * 0.7))
        alpha    = int(220 * (1.0 - progress))
        surf     = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.colour[:3], alpha), (radius, radius), radius)
        screen.blit(surf, (self.x - radius, self.y - radius))

        # Inner bright ring
        inner_r = max(2, int(radius * 0.4))
        inner_a = int(180 * (1.0 - progress))
        surf2   = pygame.Surface((inner_r * 2, inner_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf2, (255, 255, 255, inner_a), (inner_r, inner_r), inner_r)
        screen.blit(surf2, (self.x - inner_r, self.y - inner_r))


# ── Spark particles ───────────────────────────────────────────────────────────

class Spark:
    def __init__(self, x, y, colour):
        self.x      = float(x)
        self.y      = float(y)
        self.colour = colour
        angle       = random.uniform(0, math.pi * 2)
        speed       = random.uniform(2, 6)
        self.vx     = math.cos(angle) * speed
        self.vy     = math.sin(angle) * speed
        self.life   = random.randint(12, 24)
        self.age    = 0

    @property
    def alive(self):
        return self.age < self.life

    def update(self):
        self.age += 1
        self.x   += self.vx
        self.y   += self.vy
        self.vy  += 0.3   # gravity

    def draw(self, screen):
        alpha  = int(255 * (1.0 - self.age / self.life))
        radius = max(1, int(3 * (1.0 - self.age / self.life)))
        surf   = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.colour[:3], alpha), (radius + 1, radius + 1), radius)
        screen.blit(surf, (int(self.x) - radius, int(self.y) - radius))


# ── VFX Manager ───────────────────────────────────────────────────────────────

class VFXManager:
    def __init__(self, font=None):
        self.font     = font
        self.effects  = []   # HitFlash + Spark
        self.numbers  = []   # FloatingNumber

    def spawn_hit(self, x, y, damage, element_type=None, is_special=False):
        """Spawn a hit flash + sparks + floating damage number at (x, y)."""
        colour = ABILITY_FLASH_COLOURS.get(element_type, ABILITY_FLASH_COLOURS["default"])
        size   = 90 if is_special else 60

        self.effects.append(HitFlash(x, y, colour, size))

        n_sparks = 14 if is_special else 8
        for _ in range(n_sparks):
            self.effects.append(Spark(x, y, colour))

        # Damage number colour — red for enemies taking damage, gold for specials
        num_col = (255, 200, 0) if is_special else (255, 60, 60)
        self.numbers.append(FloatingNumber(
            x - 20, y - 40,
            f"-{damage}",
            num_col,
            self.font
        ))

    def spawn_super_effective(self, x, y):
        """Spawn extra sparks for a super effective hit."""
        for _ in range(10):
            self.effects.append(Spark(x, y, (120, 255, 100)))

    def spawn_heal(self, x, y, amount):
        """Green floating number for heals."""
        self.numbers.append(FloatingNumber(
            x, y, f"+{amount}", (80, 220, 80), self.font
        ))

    def update(self):
        self.effects = [e for e in self.effects if e.alive]
        self.numbers = [n for n in self.numbers if n.alive]
        for e in self.effects:
            e.update()
        for n in self.numbers:
            n.update()

    def draw(self, screen):
        for e in self.effects:
            e.draw(screen)
        for n in self.numbers:
            n.draw(screen)


# ── Idle bob animation ────────────────────────────────────────────────────────

class IdleAnimator:
    """
    Gives each sprite a subtle vertical bob using a sine wave.
    Each combatant gets a unique phase offset so they don't all move in sync.
    """
    def __init__(self, amplitude=5, speed=2.0):
        self.amplitude = amplitude
        self.speed     = speed
        self._phases   = {}   # creature id → phase offset
        self._time     = 0.0

    def register(self, creature):
        cid = id(creature)
        if cid not in self._phases:
            self._phases[cid] = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self._time += dt * self.speed

    def get_offset(self, creature):
        """Return (0, y_offset) for this creature's current bob position."""
        cid   = id(creature)
        phase = self._phases.get(cid, 0)
        y_off = int(math.sin(self._time + phase) * self.amplitude)
        return (0, y_off)