"""
Central registry — player characters, enemies, bosses.
Evolution unlocks a 4th ability and boosts stats.
Difficulty scales with evolution_stage (0=base, 1=evolved).
"""

import copy
from entities.creature import Creature
from entities.enemy import Enemy
from abilities.ability import Ability
from abilities.effects import Burn, Drain, VoidCorruption
from systems.ai import BasicAI


STAGE_DMG_SCALE = [1.0, 1.25, 1.55, 1.90]

STAGE_4TH = {
    "fire": [
        None,
        Ability("Solar Flare",   80, Burn(12, 4), cooldown=5, element="fire"),
        Ability("Magma Surge",  105, Burn(15, 4), cooldown=5, element="fire"),
        Ability("Stellar Nova", 135, Burn(18, 5), cooldown=5, element="fire"),
    ],
    "water": [
        None,
        Ability("Tsunami",       75, cooldown=5, element="water"),
        Ability("Maelstrom O",  100, cooldown=5, element="water"),
        Ability("Abyssal Surge",130, cooldown=5, element="water"),
    ],
    "nature": [
        None,
        Ability("World Tree",    70, Burn(10, 5), cooldown=5, element="nature"),
        Ability("Ancient Grove", 95, Burn(13, 5), cooldown=5, element="nature"),
        Ability("Genesis Bloom",125, Burn(16, 6), cooldown=5, element="nature"),
    ],
    "void": [
        None,
        Ability("Entropy",       75, cooldown=5, element="void"),
        Ability("Oblivion",     100, Drain(0.25), cooldown=5, element="void"),
        Ability("Annihilation", 130, Drain(0.25), cooldown=5, element="void"),
    ],
}


def make_player_abilities(character, stage=0):
    sc = STAGE_DMG_SCALE[min(stage, 3)]
    base_defs = {
        "fire": [
            ("Ember Strike", 18, dict(cooldown=1, element="fire")),
            ("Flame Burst",  30, dict(cooldown=2, element="fire")),
            ("Inferno",      55, dict(status=Burn(8, 3), cooldown=5, element="fire")),
        ],
        "water": [
            ("Water Whip",   18, dict(cooldown=1, element="water")),
            ("Tidal Wave",   28, dict(cooldown=2, element="water")),
            ("Maelstrom",    52, dict(cooldown=5, element="water")),
        ],
        "nature": [
            ("Vine Lash",    16, dict(cooldown=1, element="nature")),
            ("Thorn Shot",   26, dict(cooldown=2, element="nature")),
            ("Nature Wrath", 50, dict(status=Burn(6, 4), cooldown=5, element="nature")),
        ],
        "void": [
            ("Null Strike",   17, dict(cooldown=1, element="void")),
            ("Rift Tear",     28, dict(cooldown=2, element="void")),
            ("Void Collapse", 52, dict(status=Drain(0.25), cooldown=5, element="void")),
        ],
    }
    defs = base_defs.get(character, base_defs["void"])
    abilities = []
    for name, dmg, kwargs in defs:
        kw     = dict(kwargs)
        status = kw.pop("status", None)
        ab     = Ability(name, int(dmg * sc),
                         copy.deepcopy(status) if status else None, **kw)
        abilities.append(ab)
    if stage >= 1:
        template = STAGE_4TH.get(character, STAGE_4TH["void"])[min(stage, 3)]
        if template:
            abilities.append(copy.deepcopy(template))
    return abilities


CHARACTER_DATA = {
    "fire": {
        "element": "fire",
        "stages": [
            {"name": "Blaze",       "hp": 130, "img": "fire"},
            {"name": "Cinderstorm", "hp": 175, "img": "fire_evo1"},
            {"name": "Pyroclast",   "hp": 220, "img": "fire_evo2"},
            {"name": "Solarwraith", "hp": 270, "img": "fire_evo3"},
        ],
    },
    "water": {
        "element": "water",
        "stages": [
            {"name": "Torrent",   "hp": 150, "img": "water"},
            {"name": "Abyssal",   "hp": 195, "img": "water_evo1"},
            {"name": "Tidewyrm",  "hp": 240, "img": "water_evo2"},
            {"name": "Leviathan", "hp": 290, "img": "water_evo3"},
        ],
    },
    "nature": {
        "element": "nature",
        "stages": [
            {"name": "Thicket",    "hp": 140, "img": "nature"},
            {"name": "Verdant",    "hp": 185, "img": "nature_evo1"},
            {"name": "Overgrowth", "hp": 230, "img": "nature_evo2"},
            {"name": "Worldroot",  "hp": 280, "img": "nature_evo3"},
        ],
    },
    "void": {
        "element": "void",
        "stages": [
            {"name": "Voidling",     "hp": 135, "img": "void"},
            {"name": "Nullshade",    "hp": 178, "img": "void_evo1"},
            {"name": "Abyssal Echo", "hp": 224, "img": "void_evo2"},
            {"name": "The Unbound",  "hp": 275, "img": "void_evo3"},
        ],
    },
}


def get_stage_data(character, stage):
    stages = CHARACTER_DATA[character]["stages"]
    return stages[min(stage, len(stages) - 1)]


def make_player(character="void", stage=0):
    d = CHARACTER_DATA.get(character, CHARACTER_DATA["void"])
    s = get_stage_data(character, stage)
    return Creature(
        name=s["name"], max_health=s["hp"],
        abilities=make_player_abilities(character, stage=stage),
        image_path=s["img"], element=d["element"],
    )


def restore_player(character, save_data):
    stage    = save_data.get("evolution_stage", 0)
    player   = make_player(character, stage=stage)
    hp_bonus = save_data.get("level_hp_bonus", 0)
    player.max_health += hp_bonus
    player.health = min(player.max_health,
                        max(1, save_data.get("player_hp", player.max_health)))
    return player


BIOME_DATA = {
    "forest": {
        "bg_key": "bg_forest", "music": "forest", "label": "Forest", "element": "nature",
        "enemy_tiers": [
            ("Thornback",   "forest_enemy",  90,  "nature"),
            ("Briarwarden", "forest_enemy2", 125, "nature"),
            ("Rootstalker", "forest_enemy3", 165, "nature"),
        ],
        "boss_name": "Sylvan Dread",    "boss_img": "forest_boss", "boss_hp": 200, "boss_element": "nature",
    },
    "lava": {
        "bg_key": "bg_lava", "music": "lava", "label": "Lava Lands", "element": "fire",
        "enemy_tiers": [
            ("Cinderclaw",   "lava_enemy",  100, "fire"),
            ("Magmaserpent", "lava_enemy2", 140, "fire"),
            ("Pyreguard",    "lava_enemy3", 180, "fire"),
        ],
        "boss_name": "Magmarch",        "boss_img": "lava_boss",   "boss_hp": 220, "boss_element": "fire",
    },
    "ocean": {
        "bg_key": "bg_ocean", "music": "ocean", "label": "Ocean Depths", "element": "water",
        "enemy_tiers": [
            ("Tidecaller",  "ocean_enemy",  95,  "water"),
            ("Rip Current", "ocean_enemy2", 135, "water"),
            ("Abyssal Eel", "ocean_enemy3", 175, "water"),
        ],
        "boss_name": "Abyssarch",       "boss_img": "ocean_boss",  "boss_hp": 230, "boss_element": "water",
    },
    "ruins": {
        "bg_key": "bg_ruins", "music": "ruins", "label": "Ancient Ruins", "element": None,
        "enemy_tiers": [
            ("Voidbound",  "enemy",        85,  None),
            ("Nullshard",  "ruins_enemy2", 120, None),
            ("Voidreaper", "ruins_enemy3", 160, None),
        ],
        "boss_name": "The Null Throne", "boss_img": "boss",        "boss_hp": 240, "boss_element": None,
    },
}


def get_biome_enemy_tier(biome_key, wins):
    tiers = BIOME_DATA[biome_key]["enemy_tiers"]
    return tiers[min(wins, len(tiers) - 1)]


# Full pool of enemies for explore — all tiers accessible
EXPLORE_ENEMY_POOL = [
    {"name": "Thornback",   "img": "forest_enemy",  "hp": 90,  "element": "nature", "tier": 1},
    {"name": "Cinderclaw",  "img": "lava_enemy",    "hp": 100, "element": "fire",   "tier": 1},
    {"name": "Tidecaller",  "img": "ocean_enemy",   "hp": 95,  "element": "water",  "tier": 1},
    {"name": "Voidbound",   "img": "enemy",         "hp": 85,  "element": None,     "tier": 1},
    {"name": "Briarwarden", "img": "forest_enemy2", "hp": 125, "element": "nature", "tier": 2},
    {"name": "Magmaserpent","img": "lava_enemy2",   "hp": 140, "element": "fire",   "tier": 2},
    {"name": "Rip Current", "img": "ocean_enemy2",  "hp": 135, "element": "water",  "tier": 2},
    {"name": "Nullshard",   "img": "ruins_enemy2",  "hp": 120, "element": None,     "tier": 2},
    {"name": "Rootstalker", "img": "forest_enemy3", "hp": 165, "element": "nature", "tier": 3},
    {"name": "Pyreguard",   "img": "lava_enemy3",   "hp": 180, "element": "fire",   "tier": 3},
    {"name": "Abyssal Eel", "img": "ocean_enemy3",  "hp": 175, "element": "water",  "tier": 3},
    {"name": "Voidreaper",  "img": "ruins_enemy3",  "hp": 160, "element": None,     "tier": 3},
]


def make_explore_enemy(evolution_stage=0):
    """Random enemy from the full explore pool — all tiers possible."""
    import random
    t     = random.choice(EXPLORE_ENEMY_POOL)
    ai    = BasicAI()
    scale = 1.0 + (evolution_stage * 0.25)
    elem  = t["element"]
    tier_dmg = 1.0 + (t["tier"] - 1) * 0.15
    return [Enemy(
        name=t["name"], max_health=int(t["hp"] * scale),
        abilities=[
            Ability("Strike",     int(20 * scale * tier_dmg), cooldown=1, element=elem),
            Ability("Wild Slash", int(32 * scale * tier_dmg), cooldown=3, element=elem),
            Ability("Rampage",    int(48 * scale * tier_dmg), cooldown=5, element=elem),
        ],
        image_path=t["img"], element=elem, ai=ai, battle_tier=t["tier"],
    )]


def make_random_enemy(evolution_stage=0):
    """Ambush encounters — tier 1 only, weaker."""
    import random
    AMBUSH_POOL = [e for e in EXPLORE_ENEMY_POOL if e["tier"] == 1]
    t     = random.choice(AMBUSH_POOL)
    ai    = BasicAI()
    scale = 1.0 + (evolution_stage * 0.25)
    elem  = t["element"]
    return [Enemy(
        name=t["name"], max_health=int(t["hp"] * scale),
        abilities=[
            Ability("Ambush",       int(22 * scale), cooldown=1, element=elem),
            Ability("Feral Strike", int(35 * scale), cooldown=3, element=elem),
        ],
        image_path=t["img"], element=elem, ai=ai, battle_tier=1,
    )]


def make_enemy_party(biome_key, is_boss=False, evolution_stage=0, wins=0):
    data  = BIOME_DATA[biome_key]
    ai    = BasicAI()
    scale = 1.0 + (evolution_stage * 0.35)
    if is_boss:
        elem = data["boss_element"]
        return [Enemy(
            name=data["boss_name"], max_health=int(data["boss_hp"] * scale),
            abilities=[
                Ability("Heavy Blow", int(30 * scale), cooldown=1, element=elem),
                Ability("Crush",      int(45 * scale), cooldown=3, element=elem),
                Ability("Devastate",  int(70 * scale), cooldown=5, element=elem),
            ],
            image_path=data["boss_img"], element=data["boss_element"], ai=ai,
        )]
    else:
        e_name, e_img, e_hp, e_elem = get_biome_enemy_tier(biome_key, wins)
        tier = min(wins + 1, 3)
        return [Enemy(
            name=e_name, max_health=int(e_hp * scale),
            abilities=[
                Ability("Strike",     int(20 * scale), cooldown=1, element=e_elem),
                Ability("Wild Slash", int(32 * scale), cooldown=3, element=e_elem),
                Ability("Rampage",    int(48 * scale), cooldown=5, element=e_elem),
            ],
            image_path=e_img, element=e_elem, ai=ai, battle_tier=tier,
        )]