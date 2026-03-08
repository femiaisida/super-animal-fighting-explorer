"""
Story system — all narrative content for Super Animal Fighting Explorer.

Prophecy: The four elemental biomes have fallen into chaos. An ancient darkness
called the Voidcorrupt has seeped into each realm, twisting its creatures and
corrupting the Elemental Guardians who once kept the world in balance.
A chosen creature — marked by the Old Ones — must travel each biome,
defeat the corrupted Guardians, and restore the elemental seals before
the Voidcorrupt consumes the world entirely.
"""

# ── Opening story intro (post character select) ───────────────────────────────

STORY_INTRO_PAGES = [
    {
        "title": "In the beginning...",
        "lines": [
            "The world of Animalara was shaped by four elemental forces:",
            "Fire, Water, Nature, and the Void between them.",
            "For centuries, four Guardian Beasts kept this balance.",
            "They were protectors. They were legends.",
            "They were... corrupted.",
        ],
        "colour": (180, 140, 255),
    },
    {
        "title": "The Voidcorrupt Rises",
        "lines": [
            "From the deep ruins beneath the world, a darkness stirred.",
            "The Voidcorrupt — an ancient, formless hunger —",
            "spread through the elemental realms like a poison.",
            "Forest. Ocean. Lava. Ruins.",
            "One by one, the Guardians fell under its shadow.",
        ],
        "colour": (100, 80, 200),
    },
    {
        "title": "The Prophecy Speaks",
        "lines": [
            "The Old Ones foresaw this age of ruin.",
            "They left a single promise carved in starlight:",
            "",
            "\"When the seals break and darkness calls,",
            " a chosen creature shall rise — alone —",
            " and restore what was lost.\"",
        ],
        "colour": (255, 210, 80),
    },
    {
        "title": "That creature... is you.",
        "lines": [
            "You do not know why you were chosen.",
            "You only know the pull — a fire in your chest,",
            "a voice in the wind, a current beneath your feet.",
            "The biomes are calling.",
            "The Guardians are waiting.",
            "Your journey begins now.",
        ],
        "colour": (120, 220, 120),
    },
]

# ── Character-specific intro lines (appended after generic intro) ──────────────

CHARACTER_INTRO = {
    "fire": [
        "Blaze — a creature born from a dying ember,",
        "raised in the volcanic foothills of the Lava Lands.",
        "Hot-headed. Fearless. Chosen by flame.",
    ],
    "water": [
        "Torrent — swift as a river in full flood,",
        "emerging from the deep ocean caves of the coast.",
        "Calm on the surface. Devastating beneath.",
    ],
    "nature": [
        "Thicket — grown from the oldest seed in the Ancient Forest,",
        "patient, rooted, and quietly unstoppable.",
        "The forest remembers. And so does Thicket.",
    ],
    "void": [
        "Voidling — not born. Not summoned. Simply... present.",
        "Where you came from, there is no light, no memory, no name.",
        "The prophecy did not account for you.",
        "Neither did the darkness.",
    ],
}

# ── Biome intro cutscenes (shown first time player enters a biome) ────────────

BIOME_INTROS = {
    "forest": {
        "title": "The Corrupted Forest",
        "lines": [
            "The Ancient Forest was once a sanctuary of life.",
            "Now the trees twist in unnatural shapes,",
            "their roots pulling creatures underground.",
            "Somewhere in the canopy, the Forest Guardian waits —",
            "its mind no longer its own.",
        ],
        "colour": (80, 200, 80),
    },
    "lava": {
        "title": "The Burning Lands",
        "lines": [
            "The Lava Lands were always harsh. But never like this.",
            "The eruptions are constant now. The sky chokes with ash.",
            "Fire creatures who once lived in peace",
            "now attack anything that breathes.",
            "The Lava King has gone silent. That is never good.",
        ],
        "colour": (255, 100, 30),
    },
    "ocean": {
        "title": "Ocean Depths",
        "lines": [
            "The ocean was always vast. Now it is angry.",
            "The tides have reversed. The deep glows with dark light.",
            "Ancient creatures surface who should never see sky.",
            "The Kraken stirs at the bottom of everything,",
            "waiting for a challenger foolish enough to dive deep.",
        ],
        "colour": (40, 140, 255),
    },
    "ruins": {
        "title": "The Ancient Ruins",
        "lines": [
            "No one builds here anymore. No one dares.",
            "The ruins are older than memory —",
            "built by a civilisation that vanished when the Voidcorrupt first woke.",
            "Their guardians never stopped guarding.",
            "The Ruins Overlord has waited a thousand years for this fight.",
        ],
        "colour": (200, 160, 100),
    },
}

# ── Boss pre-fight dialogue ────────────────────────────────────────────────────

# Boss taunts keyed to the NEW boss names in data/creatures.py
BOSS_TAUNTS = {
    # ── Sylvan Dread — ancient, corrupted, speaks like nature itself ──────
    "Sylvan Dread": [
        "\"The roots remember everything.\"",
        "\"Every creature that entered this forest is still here.\nPart of the soil. Part of me.\"",
        "\"You smell like the old world. The world before the Voidcorrupt.\nThat world is gone.\"",
        "\"I did not choose this darkness. But I have grown into it.\nAs you will.\"",
    ],
    # ── Magmarch — furious, proud, military general of fire ──────────────
    "Magmarch": [
        "\"HALT.\"",
        "\"I have stood at this pass for four hundred years.\nNOTHING has crossed.\"",
        "\"The Voidcorrupt did not corrupt me. It PROMOTED me.\"",
        "\"You want to fight the darkness? You must first get through the fire.\nNobody gets through the fire.\"",
    ],
    # ── Abyssarch — ancient, slow, cold, barely aware of you ─────────────
    "Abyssarch": [
        "\"...\"",
        "\"(Something massive shifts far below.)\"",
        "\"(The pressure changes. The water darkens.)\"",
        "\"You are very small.\"",
        "\"The ocean does not hate you.\nIt simply does not notice you.\"",
    ],
    # ── The Null Throne — ancient philosopher, almost sympathetic ─────────
    "The Null Throne": [
        "\"You made it. I confess I did not expect that.\"",
        "\"I have sat here for eleven hundred years\nwatching the world above decay.\"",
        "\"The Voidcorrupt is not evil. It is simply entropy.\nTime. The end of all things.\"",
        "\"The prophecy says you will restore the seals.\nPerhaps. I have seen prophecies fail before.\"",
        "\"Let us find out together.\"",
    ],
}

# ── Map narration (shown between biomes as story progress) ─────────────────────

MAP_NARRATION = {
    0: [   # After starting
        "The world feels different now that you have stepped into it.",
        "The pull of the prophecy grows stronger.",
        "Four seals. Four Guardians. One chance.",
    ],
    1: [   # After 1 boss kill
        "One seal restored. The Voidcorrupt recoils — briefly.",
        "You can feel the change in the air. Something is watching.",
        "Three remain.",
    ],
    2: [   # After 2 boss kills
        "Two seals glow with restored light.",
        "Creatures in the safe zones whisper your name.",
        "The darkness is no longer passive. It has noticed you.",
    ],
    3: [   # After 3 boss kills
        "Three seals burn bright. One last realm waits.",
        "The Voidcorrupt is desperate now.",
        "You can hear it in every shadow. It is afraid.",
    ],
    4: [   # All cleared
        "The four seals ignite.",
        "The Voidcorrupt screams — a sound like a world ending.",
        "And then... silence.",
        "It is done.",
    ],
}

# ── NPC Messenger lines (random, shown on map) ────────────────────────────────

# Each entry: (name, [list of dialogue lines in order], sprite_key)
# Player cycles through lines on repeat visits
NPC_DIALOGUE = {
    "npc_elder": ("Wandering Elder", [
        "\"The Voidcorrupt feeds on fear.\nFace it with courage and it weakens.\"",
        "\"Every Guardian was once something innocent.\nDo not forget that.\"",
        "\"I have walked these lands for sixty years.\nI have never seen the sky this dark.\"",
        "\"Rest when you can. The road ahead is long.\"",
    ], "npc_elder"),
    "npc_fox": ("Shadow Fox", [
        "\"I have been watching you.\nThe Guardians were not always monsters.\nRemember that when you face them.\"",
        "\"The forest has eyes. So do I.\nYou are not as alone as you think.\"",
        "\"Three others tried the prophecy before you.\nThey did not come back.\nYou seem... different.\"",
        "\"I hear things. The Voidcorrupt is afraid of you.\nGood.\"",
    ], "npc_fox"),
    "npc_scout": ("Injured Scout", [
        "\"The forest... it spoke to me.\nIt said a chosen one was coming.\nI did not believe it until now.\"",
        "\"My wounds are from Thornback.\nHit me before I even saw it.\nWatch your flanks.\"",
        "\"I tried to reach the ruins once.\nTurned back at the lava fields.\nYou will need fire resistance, or speed.\"",
        "\"Still here. Still fighting.\nThat is all any of us can do.\"",
    ], "npc_scout"),
    "npc_turtle": ("Ancient Turtle", [
        "\"I have lived three hundred years.\nI have seen the Voidcorrupt before.\nIt was beaten once. It can be beaten again.\"",
        "\"Patience. The ocean did not carve the canyon in a day.\nNeither will you defeat evil in a rush.\"",
        "\"I knew the ones who wrote the prophecy.\nThey were not optimists.\nThey wrote it as a warning, not a promise.\"",
        "\"You are still here.\nThat already puts you ahead of most.\"",
    ], "npc_turtle"),
    "npc_ember": ("Young Ember", [
        "\"Are you the one from the prophecy?\nYou do not look like a legend.\nBut I suppose legends rarely do.\"",
        "\"I want to fight too.\nThey say I am too young.\nI say the darkness does not check your age.\"",
        "\"You defeated another Guardian?\nThat is incredible!\nWill you teach me how?\"",
        "\"Stay safe out there.\nI mean it.\nWe need you to come back.\"",
    ], "npc_ember"),
    "npc_sprite": ("Corrupted Sprite", [
        "\"Help... me...\nThe darkness... it is inside...\nDo not let it... spread further...\"",
        "\"I remember... what it felt like... to be free.\nThat memory is all I have left.\nDo not let it happen to others.\"",
        "\"It is getting... harder to resist.\nEvery hour...\nPlease hurry.\"",
        "\"If I go completely...\npromise me...\nyou will not hesitate.\"",
    ], "npc_sprite"),
    "npc_hawk": ("Sky Hawk", [
        "\"From above I can see the corruption spreading.\nYou must hurry.\nThe ruins are the source. I am certain of it.\"",
        "\"I saw you fight from the sky.\nNot bad.\nYou move like someone who wants to survive.\"",
        "\"The corruption reached the outer forest.\nIt is moving faster now.\nSomething is feeding it.\"",
        "\"Wind is changing direction.\nThat is never good this time of year.\nOr any year, lately.\"",
    ], "npc_hawk"),
}

NPC_KEYS = list(NPC_DIALOGUE.keys())

# ── Evolution story text ───────────────────────────────────────────────────────

# Stage 1 = first evolution, stage 2 = second evolution
EVOLUTION_TEXT = {
    "fire": {
        1: {
            "before": [
                "As the Guardian's darkness fades, a warmth floods your body.",
                "Not just heat — something older. A recognition.",
                "The flame inside you answers.",
            ],
            "after": [
                "You are no longer just Blaze.",
                "You are Cinderstorm — a force of living fire.",
                "The prophecy has chosen well.",
            ],
        },
        2: {
            "before": [
                "You have burned through every doubt.",
                "The second seal breaks open. Fire does not grow.",
                "It transforms. And so do you.",
            ],
            "after": [
                "Cinderstorm was a spark compared to this.",
                "You are now Pyroclast — the fire that ended a world.",
                "Even the Voidcorrupt will feel the heat.",
            ],
        },
    },
    "water": {
        1: {
            "before": [
                "The ocean sings. You have never heard it so clearly.",
                "A current rises through you — the deep current,",
                "the one that moves beneath all tides.",
            ],
            "after": [
                "Torrent was the stream. This is the flood.",
                "You are now Abyssal — the living deep.",
                "The prophecy stirs in the water's memory.",
            ],
        },
        2: {
            "before": [
                "The second seal cracks and the deep answer.",
                "Not just the ocean — the water beneath the ocean.",
                "The pressure here would crush anything lesser.",
            ],
            "after": [
                "Abyssal touched the deep. You have become it.",
                "You are now Tidewyrm — the ocean's final form.",
                "Nothing that enters the deep returns unchanged.",
            ],
        },
    },
    "nature": {
        1: {
            "before": [
                "The roots of every tree in the forest reach toward you.",
                "Ancient memory flows through bark and soil.",
                "You remember things you have never seen.",
            ],
            "after": [
                "Thicket shed its shell like bark from a growing tree.",
                "You are now Verdant — the living forest given form.",
                "The oldest prophecy was written in your rings.",
            ],
        },
        2: {
            "before": [
                "The forest is not the trees. It is what lives between them.",
                "You have learned the shape of that space.",
                "The second seal dissolves like frost at dawn.",
            ],
            "after": [
                "Verdant was the forest. This is the wild itself.",
                "You are now Overgrowth — ancient before the seals existed.",
                "The Voidcorrupt fears what it cannot corrupt.",
            ],
        },
    },
    "void": {
        1: {
            "before": [
                "The darkness does not flood you. It recognises you.",
                "You were never separate from it.",
                "The void does not change you — it reveals you.",
            ],
            "after": [
                "Voidling was only the surface.",
                "What you are now has no name in any living language.",
                "The prophecy did not predict this. Nothing did.",
            ],
        },
        2: {
            "before": [
                "The second seal does not break. It simply ceases to exist.",
                "You did not cross a threshold. You erased it.",
                "Even the void holds its breath.",
            ],
            "after": [
                "Nullshade was a shadow of this.",
                "You are now Abyssal Echo — the silence at the end of everything.",
                "The prophecy has no words for what comes next.",
            ],
        },
    },
}


def get_evolution_text(character, stage):
    """Return before/after text dict for the given character and evolution stage (1 or 2)."""
    char_data = EVOLUTION_TEXT.get(character, EVOLUTION_TEXT.get("void", {}))
    stage_data = char_data.get(stage, char_data.get(1, {}))
    return {
        "before": stage_data.get("before", ["Something stirs within you..."]),
        "after":  stage_data.get("after",  ["You feel stronger."]),
    }

# ── Gold reward flavour text ───────────────────────────────────────────────────

GOLD_REWARDS = {
    "normal": "The creature dissolves, leaving behind a shard of elemental crystal.",
    "boss":   "The Guardian collapses. A surge of pure elemental energy crystallises around you.",
    "random": "The ambusher retreats, dropping its stash in panic.",
}


def get_map_narration(boss_kills):
    return MAP_NARRATION.get(boss_kills, [])


def get_boss_taunts(boss_name):
    return BOSS_TAUNTS.get(boss_name, [
        f"\"{boss_name} stares at you with hollow eyes.\"",
        "\"It does not speak. It simply waits.\"",
    ])


def get_npc_message(save_data=None):
    """Pick a random NPC and return the next unseen line for that NPC."""
    import random
    key = random.choice(NPC_KEYS)
    name, lines, sprite = NPC_DIALOGUE[key]
    # Track which line index to show next per NPC
    if save_data is not None:
        seen = save_data.setdefault("npc_line_index", {})
        idx  = seen.get(key, 0)
        line = lines[idx % len(lines)]
        seen[key] = (idx + 1) % len(lines)
    else:
        line = random.choice(lines)
    return (name, line, sprite)