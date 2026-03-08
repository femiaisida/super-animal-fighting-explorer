import copy
"""
Save system — persists run state to game/save.json.
"""
import json
import os

SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save.json")

DEFAULT_SAVE = {
    "player_character": "hero",
    "evolved":          False,
    "evolution_stage":  0,          # 0 = base, 1 = evolved
    "cleared_biomes":   [],
    "visited_biomes":   [],         # for biome intro cutscene (shown once)
    "biome_wins":       {},         # {biome_key: int} — normal wins per biome
    "pending_evolution":False,      # set True after boss kill, consumed by evolution scene
    "gold":             0,
    "potions":          0,
    "xp":               0,
    "level":            1,
    "level_hp_bonus":   0,    # cumulative HP from level-ups
    "run_stats": {
        "damage_dealt":    0,
        "turns_taken":     0,
        "abilities_used":  0,
        "boss_kills":      0,
        "gold_earned":     0,
        "potions_used":    0,
    },
    "player_hp":     140,
    "player_max_hp": 140,
}


def load():
    if not os.path.exists(SAVE_PATH):
        return dict(DEFAULT_SAVE)
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
        for key, val in DEFAULT_SAVE.items():
            if key not in data:
                data[key] = val
        # ensure nested run_stats keys exist
        for k, v in DEFAULT_SAVE["run_stats"].items():
            data["run_stats"].setdefault(k, v)
        return data
    except Exception as e:
        print(f"[Save] Failed to load: {e}. Using defaults.")
        return dict(DEFAULT_SAVE)


def save(data):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Save] Saved.")
    except Exception as e:
        print(f"[Save] Write error: {e}")


def delete():
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
        print("[Save] Deleted.")


def new_run(character):
    d = copy.deepcopy(DEFAULT_SAVE)
    d["player_character"] = character
    return d


def mark_biome_cleared(data, biome_key):
    if biome_key not in data["cleared_biomes"]:
        data["cleared_biomes"].append(biome_key)
    return data


def mark_biome_visited(data, biome_key):
    if biome_key not in data["visited_biomes"]:
        data["visited_biomes"].append(biome_key)
    return data


def add_gold(data, amount):
    data["gold"] = data.get("gold", 0) + amount
    data["run_stats"]["gold_earned"] = data["run_stats"].get("gold_earned", 0) + amount
    return data


def spend_gold(data, amount):
    """Returns True if purchase successful."""
    if data.get("gold", 0) >= amount:
        data["gold"] -= amount
        return True
    return False


# XP thresholds: XP needed to reach each level (cumulative)
# Levels 1-15. Evolution triggers at levels 4, 8, 12.
XP_PER_LEVEL = [0, 0, 30, 60, 100, 150, 210, 280, 360, 450, 550, 660, 780, 910, 1050]
EVOLUTION_LEVELS = {4: 1, 8: 2, 12: 3}   # level → evolution stage
XP_REWARDS = {"boss": 80, "normal": 25, "random": 15}
HP_PER_LEVEL  = 12   # HP gained per level-up
DMG_PER_LEVEL = 0.04  # 4% damage bonus per level on top of stage scaling


def get_level_from_xp(xp):
    level = 1
    for i, threshold in enumerate(XP_PER_LEVEL):
        if xp >= threshold:
            level = i + 1
        else:
            break
    return min(level, len(XP_PER_LEVEL))


def xp_for_next_level(current_level):
    if current_level >= len(XP_PER_LEVEL):
        return None
    return XP_PER_LEVEL[current_level]   # index = level number (1-indexed, so level 2 = index 2)


def add_xp(data, battle_type):
    """Award XP, update level, return (xp_gained, levelled_up, new_level, evo_stage_unlocked)."""
    gained    = XP_REWARDS.get(battle_type, 15)
    data["xp"] = data.get("xp", 0) + gained
    old_level  = data.get("level", 1)
    new_level  = get_level_from_xp(data["xp"])
    data["level"] = new_level
    levelled_up = new_level > old_level
    if levelled_up:
        # HP bonus for each level gained
        levels_gained = new_level - old_level
        data["level_hp_bonus"] = data.get("level_hp_bonus", 0) + levels_gained * HP_PER_LEVEL
    # Check if this level triggers an evolution
    evo_unlocked = None
    for level_trigger, stage in EVOLUTION_LEVELS.items():
        if old_level < level_trigger <= new_level:
            current_stage = data.get("evolution_stage", 0)
            if stage > current_stage:
                data["pending_evolution"] = True
                evo_unlocked = stage
    return gained, levelled_up, new_level, evo_unlocked


def add_biome_win(data, biome_key):
    """Increment normal win count for a biome. Returns new count."""
    wins = data.setdefault("biome_wins", {})
    wins[biome_key] = wins.get(biome_key, 0) + 1
    return wins[biome_key]

def biome_win_count(data, biome_key):
    return data.get("biome_wins", {}).get(biome_key, 0)

def add_potion(data):
    data["potions"] = data.get("potions", 0) + 1
    return data


def use_potion(data):
    """Returns True if potion was available."""
    if data.get("potions", 0) > 0:
        data["potions"] -= 1
        data["run_stats"]["potions_used"] = data["run_stats"].get("potions_used", 0) + 1
        return True
    return False


def update_stats(data, damage=0, turns=0, abilities=0, boss_kill=False):
    s = data["run_stats"]
    s["damage_dealt"]   += damage
    s["turns_taken"]    += turns
    s["abilities_used"] += abilities
    if boss_kill:
        s["boss_kills"] += 1
    return data


def all_biomes_cleared(data):
    return set(data["cleared_biomes"]) >= {"forest", "lava", "ocean", "ruins"}


def biomes_fully_cleared(data):
    """Count biomes where the boss has been defeated."""
    return sum(1 for b in ["forest","lava","ocean","ruins"]
               if b + "_boss" in data.get("cleared_biomes", []))