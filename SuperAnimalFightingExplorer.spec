# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None
GAME_DIR = Path(".")

a = Analysis(
    [str(GAME_DIR / "main.py")],
    pathex=[str(GAME_DIR)],
    binaries=[],
    datas=[(str(GAME_DIR / "assets"), "assets")],
    hiddenimports=[
        "pygame", "pygame.mixer", "pygame.font", "pygame.image",
        "pygame.transform", "pygame.display",
        "core.asset_manager", "core.scene_manager", "core.event_bus",
        "data.creatures", "entities.creature", "entities.enemy",
        "abilities.ability", "abilities.effects",
        "systems.ai", "systems.battle_controller", "systems.combat_system",
        "systems.economy", "systems.save_system", "systems.story",
        "systems.type_system", "systems.vfx",
        "scenes.loading_scene", "scenes.character_select_scene",
        "scenes.story_intro_scene", "scenes.map_scene", "scenes.battle_scene",
        "scenes.ambush_scene", "scenes.biome_intro_scene", "scenes.explore_scene",
        "scenes.evolution_scene", "scenes.npc_scene", "scenes.shop_scene",
        "scenes.win_scene", "scenes.lose_scene", "scenes.summary_scene",
        "scenes.intro_scene",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "email", "html", "http", "xml"],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="SuperAnimalFightingExplorer",
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SuperAnimalFightingExplorer",
)
