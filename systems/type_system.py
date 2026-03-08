"""
Type advantage system.
Triangle: Fire > Nature > Water > Fire
Bonus:    +25% damage
Penalty:  -25% damage
Neutral:   no change
"""

ADVANTAGES = {
    "fire":   "nature",   # fire beats nature
    "water":  "fire",     # water beats fire
    "nature": "water",    # nature beats water
}

BIOME_ENEMY_TYPES = {
    "forest": "nature",
    "lava":   "fire",
    "ocean":  "water",
    "ruins":  None,        # ruins is neutral
}

TYPE_COLOURS = {
    "fire":   (255, 120,  40),
    "water":  ( 60, 160, 255),
    "nature": ( 80, 210,  80),
    "void":   (160,  80, 255),
    None:     (180, 180, 180),
}


def get_multiplier(attacker_type, defender_type):
    """Return damage multiplier based on type matchup."""
    if not attacker_type or not defender_type:
        return 1.0
    if ADVANTAGES.get(attacker_type) == defender_type:
        return 1.25   # super effective
    if ADVANTAGES.get(defender_type) == attacker_type:
        return 0.75   # not very effective
    return 1.0


def get_matchup_text(attacker_type, defender_type):
    """Return a display string for the matchup."""
    m = get_multiplier(attacker_type, defender_type)
    if m > 1.0:
        return "SUPER EFFECTIVE!", (120, 255, 100)
    if m < 1.0:
        return "Not very effective...", (180, 120, 80)
    return "", (255, 255, 255)