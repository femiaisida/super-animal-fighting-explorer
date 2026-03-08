"""
Economy system — gold rewards, shop items, pricing.
"""
import random

POTION_COST  = 25
POTION_HEAL  = 60
ELIXIR_COST  = 50
SHIELD_COST  = 30
POWER_COST   = 35

GOLD_NORMAL  = (15, 25)
GOLD_BOSS    = (40, 60)
GOLD_RANDOM  = (10, 20)

SHOP_ITEMS = [
    {
        "key":     "potion",
        "name":    "Healing Potion",
        "desc":    f"+{POTION_HEAL} HP",
        "cost":    POTION_COST,
        "img_key": "item_potion",
        "flavour": "From the Elemental Springs.",
    },
    {
        "key":     "elixir",
        "name":    "Full Elixir",
        "desc":    "Restore all HP",
        "cost":    ELIXIR_COST,
        "img_key": "item_elixir",
        "flavour": "A rare distillation.",
    },
    {
        "key":     "shield",
        "name":    "Shield Charm",
        "desc":    "Block 50% next hit",
        "cost":    SHIELD_COST,
        "img_key": "item_shield",
        "flavour": "Ancient rune. Still warm.",
    },
    {
        "key":     "power",
        "name":    "Power Shard",
        "desc":    "+20% dmg for 3 turns",
        "cost":    POWER_COST,
        "img_key": "item_power",
        "flavour": "Crystallised rage.",
    },
]


def reward_gold(battle_type="normal"):
    if battle_type == "boss":    return random.randint(*GOLD_BOSS)
    elif battle_type == "random": return random.randint(*GOLD_RANDOM)
    return random.randint(*GOLD_NORMAL)


def can_afford(save_data, cost):
    return save_data.get("gold", 0) >= cost


def can_afford_potion(save_data):
    return can_afford(save_data, POTION_COST)


def buy_item(save_data, item_key):
    import systems.save_system as ss
    item = next((i for i in SHOP_ITEMS if i["key"] == item_key), None)
    if not item:
        return False, "Unknown item."
    if not ss.spend_gold(save_data, item["cost"]):
        return False, f"Need {item['cost']}g!"
    if item_key == "potion":
        ss.add_potion(save_data)
        return True, f"Potion purchased! You have {save_data['potions']}."
    elif item_key == "elixir":
        save_data["elixirs"] = save_data.get("elixirs", 0) + 1
        return True, "Full Elixir added!"
    elif item_key == "shield":
        save_data["shield_charges"] = save_data.get("shield_charges", 0) + 1
        return True, "Shield Charm ready!"
    elif item_key == "power":
        save_data["power_shards"] = save_data.get("power_shards", 0) + 1
        return True, "Power Shard ready!"
    return False, "Something went wrong."


def buy_potion(save_data):
    success, _ = buy_item(save_data, "potion")
    return success