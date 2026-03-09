import pygame
import random
from core.scene_manager import Scene
from systems.vfx import VFXManager, IdleAnimator
from systems.type_system import TYPE_COLOURS
from systems.economy import reward_gold, POTION_HEAL
from systems.story import get_boss_taunts
import systems.save_system as save_system

STATE_PLAYER_TURN = "player_turn"
STATE_ENEMY_TURN  = "enemy_turn"
STATE_ANIMATING   = "animating"
STATE_BOSS_INTRO  = "boss_intro"

# Base sizes — adjusted dynamically per creature tier/stage
NORMAL_SPRITE_SIZE = (220, 220)
BOSS_SPRITE_SIZE   = (260, 260)


def is_boss(creature):
    return creature.max_health >= 180


class BattleScene(Scene):
    def __init__(self, manager, player_party, enemy_party, battle_controller,
                 assets, bg_key="battle_bg", biome_key=None, is_boss_fight=False,
                 is_random=False, player_character="hero", save_data=None, origin="map"):
        super().__init__(manager)
        self.player_party      = player_party
        self.enemy_party       = enemy_party
        self.battle_controller = battle_controller

        # Always reset ALL cooldowns at battle start — no stale state from previous battles
        for _party in (player_party, enemy_party):
            for _c in _party:
                for _ab in _c.abilities:
                    _ab.current_cooldown = 0
        self.assets            = assets
        self.bg_key            = bg_key
        self.biome_key         = biome_key
        self.is_boss_fight     = is_boss_fight
        self.is_random         = is_random
        self.player_character  = player_character
        self.save_data         = save_data or save_system.load()
        self.event_bus         = battle_controller.event_bus

        # Determine music — defer actual play() to first update() tick
        # so pygame.mixer has a full frame to flush after stop_music()
        assets.stop_music()
        if is_boss_fight:
            self._pending_music = "boss"
        elif biome_key:
            from data.creatures import BIOME_DATA as _BD
            _bdata = _BD.get(biome_key, {})
            self._pending_music = _bdata.get("music", "map")
        else:
            self._pending_music = "map"
        self._music_started = False
        self.origin            = origin   # "map" or "explore"
        self.xp_gained         = 0
        self.levelled_up       = False
        self.new_level         = 1

        info    = pygame.display.Info()
        self.sw = info.current_w
        self.sh = info.current_h

        # Boss intro state
        if is_boss_fight and enemy_party:
            boss_name   = enemy_party[0].name
            self.taunts = get_boss_taunts(boss_name)
            self.state  = STATE_BOSS_INTRO
        else:
            self.taunts = []
            self.state  = STATE_PLAYER_TURN

        self.taunt_index = 0
        self.taunt_timer = 0

        self.anim_timer      = 0
        self.paused          = False
        self.shake_timer     = 0
        self.shake_offset    = (0, 0)
        self.message         = "Your turn! Choose an ability."
        self.message_timer   = 999
        self.matchup_text    = ""
        self.matchup_colour  = (255, 255, 255)
        self.matchup_timer   = 0
        self.hovered_ability = -1
        self.potion_msg      = ""
        self.potion_timer    = 0

        font_medium  = assets.get_font("medium")
        self.vfx     = VFXManager(font=font_medium)
        self.idle    = IdleAnimator(amplitude=5, speed=1.8)
        for c in self.player_party + self.enemy_party:
            self.idle.register(c)

        self.event_bus.subscribe("ABILITY_USED", self.on_ability_used)

        # Boss fight drama — phase tracking
        self.boss_phase       = 1      # 1=normal, 2=enraged (<50% HP), 3=desperate (<25% HP)
        self.boss_phase_msg   = ""
        self.boss_phase_timer = 0
        self.boss_screen_flash = 0
        self.timer            = 0     # general frame counter for animations

    # ─────────────────────────────────────────────────────────────────────────
    # Input
    # ─────────────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        # Boss intro — any key advances taunt
        if self.state == STATE_BOSS_INTRO:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) and self.taunt_timer > 30:
                self._advance_taunt()
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            self.paused = not self.paused
            return

        if self.paused:
            self._handle_pause_event(event)
            return

        if self.state != STATE_PLAYER_TURN:
            return

        player = self.player_party[0] if self.player_party else None
        if not player or not player.is_alive():
            return

        if event.type == pygame.KEYDOWN:
            key_map = {pygame.K_1:0, pygame.K_2:1, pygame.K_3:2, pygame.K_4:3, pygame.K_5:4}
            if event.key in key_map:
                self._player_use_ability(player, key_map[event.key])
            elif event.key == pygame.K_h:
                self._use_potion(player)
            elif event.key == pygame.K_j:
                self._use_elixir(player)
            elif event.key == pygame.K_s:
                self._use_shield(player)
            elif event.key == pygame.K_d:
                self._use_power(player)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            idx = self._ability_slot_at(event.pos)
            if idx is not None:
                self.assets.play_sound("click")
                self._player_use_ability(player, idx)
            if self._potion_rect().collidepoint(event.pos):
                self._use_potion(player)
            if self._elixir_rect().collidepoint(event.pos):
                self._use_elixir(player)
            if self._shield_rect().collidepoint(event.pos):
                self._use_shield(player)
            if self._power_rect().collidepoint(event.pos):
                self._use_power(player)

        if event.type == pygame.MOUSEMOTION:
            idx = self._ability_slot_at(event.pos)
            self.hovered_ability = idx if idx is not None else -1

    def _advance_taunt(self):
        self.taunt_index += 1
        self.taunt_timer  = 0
        if self.taunt_index >= len(self.taunts):
            self.state = STATE_PLAYER_TURN
            self._set_message("Your turn! Choose an ability.")

    def _handle_pause_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.paused = False
            elif event.key == pygame.K_q:
                self.assets.stop_music()
                from scenes.map_scene import MapScene
                self.manager.switch(MapScene(
                    self.manager, self.assets,
                    player_party=self.player_party,
                    player_character=self.player_character,
                    save_data=self.save_data,
                ))

    def _player_use_ability(self, player, idx):
        if idx >= len(player.abilities):
            return
        ability = player.abilities[idx]
        if not ability.is_ready():
            self._set_message(f"{ability.name} on cooldown! ({ability.current_cooldown} turns)")
            return
        targets = [e for e in self.enemy_party if e.is_alive()]
        if not targets:
            return
        self.battle_controller.perform_ability(player, ability, targets[0])
        self.assets.play_sound("attack")
        self.state      = STATE_ANIMATING
        self.anim_timer = 140

    def _use_potion(self, player):
        if save_system.use_potion(self.save_data):
            heal = min(POTION_HEAL, player.max_health - player.health)
            player.heal(POTION_HEAL)
            save_system.save(self.save_data)
            self.vfx.spawn_heal(
                self._sprite_centre(player)[0],
                self._sprite_centre(player)[1],
                heal
            )
            self.potion_msg   = f"Used a potion! +{heal} HP"
            self.potion_timer = 150
            self.assets.play_sound("click")
        else:
            self.potion_msg   = "No potions left! Buy some at the shop."
            self.potion_timer = 120

    def _use_elixir(self, player):
        elixirs = self.save_data.get("elixirs", 0)
        if elixirs > 0:
            heal = player.max_health - player.health
            player.heal(player.max_health)
            self.save_data["elixirs"] = elixirs - 1
            save_system.save(self.save_data)
            self.vfx.spawn_heal(
                self._sprite_centre(player)[0],
                self._sprite_centre(player)[1],
                heal
            )
            self.potion_msg   = f"Full Elixir used! HP fully restored!"
            self.potion_timer = 180
            self.assets.play_sound("potion")
        else:
            self.potion_msg   = "No Elixirs! Buy one at the shop."
            self.potion_timer = 120

    # ─────────────────────────────────────────────────────────────────────────
    # Event bus
    # ─────────────────────────────────────────────────────────────────────────

    def _use_shield(self, player):
        if self.state != STATE_PLAYER_TURN: return
        charges = self.save_data.get("shield_charges", 0)
        if charges <= 0:
            self._set_message("No Shield Charges!")
            return
        # Shield: reduce incoming damage this turn (stored as a flag)
        player.shield_active = True
        self.save_data["shield_charges"] = charges - 1
        self.potion_msg   = "Shield activated! Next hit reduced."
        self.potion_timer = 120
        self.assets.play_sound("click")

    def _use_power(self, player):
        if self.state != STATE_PLAYER_TURN: return
        shards = self.save_data.get("power_shards", 0)
        if shards <= 0:
            self._set_message("No Power Shards!")
            return
        # Power: boost next ability damage by 50%
        player.power_boost = True
        self.save_data["power_shards"] = shards - 1
        self.potion_msg   = "Power surging! Next ability +50% damage."
        self.potion_timer = 120
        self.assets.play_sound("click")

    def on_ability_used(self, data):
        self.shake_timer = 14
        self.assets.play_sound("hit")
        tx, ty   = self._sprite_centre(data["target"])
        is_spec  = getattr(data["ability"], "cooldown", 0) >= 5
        elem     = getattr(data["ability"], "element", None) or getattr(data["user"], "element", None)
        self.vfx.spawn_hit(tx, ty, data["damage"], element_type=elem, is_special=is_spec)
        if data.get("multiplier", 1.0) > 1.0:
            self.vfx.spawn_super_effective(tx, ty)
        self._set_message(
            f"{data['user'].name} used {data['ability'].name}!  -{data['damage']} HP")
        if data.get("matchup_text"):
            self.matchup_text   = data["matchup_text"]
            self.matchup_colour = data["matchup_colour"]
            self.matchup_timer  = 90

    def _sprite_centre(self, creature):
        sh       = self.sh
        sprite_y = int(sh * 0.32)
        if creature in self.player_party:
            i = self.player_party.index(creature)
            x = int(self.sw * 0.10) + i * 180
        else:
            i = self.enemy_party.index(creature)
            x = int(self.sw * 0.68) - i * 220
        sz = BOSS_SPRITE_SIZE if is_boss(creature) else NORMAL_SPRITE_SIZE
        return (x + sz[0]//2, sprite_y + sz[1]//2)

    # ─────────────────────────────────────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────────────────────────────────────

    def update(self, dt):
        self.timer += 1

        # Start music on first update — one full frame after stop_music() ensures no bleed
        if not self._music_started:
            self._music_started = True
            self.assets.play_music(self._pending_music)

        if self.state == STATE_BOSS_INTRO:
            self.taunt_timer += 1
            return

        if self.paused:
            return

        self.idle.update(dt)
        self.vfx.update()

        if self.matchup_timer  > 0: self.matchup_timer  -= 1
        if self.potion_timer   > 0: self.potion_timer   -= 1

        if self.battle_controller.all_enemies_defeated():
            self.assets.stop_music()
            self.assets.play_sound("victory")
            self._handle_victory()
            return

        if self.battle_controller.all_players_defeated():
            self.assets.stop_music()
            from scenes.lose_scene import LoseScene
            self._flush_stats()
            self.manager.switch(LoseScene(self.manager, self.assets,
                                          save_data=self.save_data, origin=self.origin))
            return

        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_offset = (random.randint(-6,6), random.randint(-4,4))
        else:
            self.shake_offset = (0,0)

        # Boss phase transitions
        if self.is_boss_fight and self.enemy_party:
            boss = self.enemy_party[0]
            if boss.is_alive():
                ratio = boss.health / boss.max_health
                if ratio <= 0.25 and self.boss_phase < 3:
                    self.boss_phase       = 3
                    self.boss_phase_msg   = f"{boss.name} is DESPERATE!"
                    self.boss_phase_timer = 200
                    self.boss_screen_flash = 30
                elif ratio <= 0.5 and self.boss_phase < 2:
                    self.boss_phase       = 2
                    self.boss_phase_msg   = f"{boss.name} is ENRAGED!"
                    self.boss_phase_timer = 200
                    self.boss_screen_flash = 20

        if self.boss_phase_timer  > 0: self.boss_phase_timer  -= 1
        if self.boss_screen_flash > 0: self.boss_screen_flash -= 1

        if self.state == STATE_ANIMATING:
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                self.state = STATE_ENEMY_TURN

        if self.state == STATE_ENEMY_TURN:
            self._run_enemy_turn()

    def _handle_victory(self):
        from scenes.win_scene import WinScene

        # Gold reward
        battle_type = "boss" if self.is_boss_fight else "random" if self.is_random else "normal"
        gold_earned = reward_gold(battle_type)
        save_system.add_gold(self.save_data, gold_earned)
        self._set_message(f"Victory! +{gold_earned}g")

        if self.is_boss_fight and self.biome_key:
            save_system.mark_biome_cleared(self.save_data, self.biome_key + "_boss")
            save_system.mark_biome_cleared(self.save_data, self.biome_key)
            self.save_data["run_stats"]["boss_kills"] = \
                self.save_data["run_stats"].get("boss_kills", 0) + 1
            # Full HP restore after boss victory
            if self.player_party:
                player = self.player_party[0]
                player.health = player.max_health
                self.save_data["player_hp"] = player.max_health
        elif self.biome_key:
            save_system.add_biome_win(self.save_data, self.biome_key)

        # Award XP — evolution is triggered by level, not by boss kills
        xp_type = "boss" if self.is_boss_fight else "random" if self.is_random else "normal"
        xp_gained, levelled_up, new_level, _evo = save_system.add_xp(self.save_data, xp_type)
        self.xp_gained   = xp_gained
        self.levelled_up = levelled_up
        self.new_level   = new_level

        # Partial heal after every non-boss fight (20% of max HP)
        if not self.is_boss_fight and self.player_party:
            player     = self.player_party[0]
            heal_amt   = max(10, int(player.max_health * 0.20))
            player.heal(heal_amt)
            self.save_data["player_hp"] = player.health

        self._flush_stats()
        save_system.save(self.save_data)
        all_done = save_system.all_biomes_cleared(self.save_data)

        self.manager.switch(WinScene(
            self.manager, self.assets,
            player_party=self.player_party,
            player_character=self.player_character,
            save_data=self.save_data,
            is_boss_victory=self.is_boss_fight,
            is_random=self.is_random,
            run_complete=all_done,
            gold_earned=gold_earned,
            origin=self.origin,
            xp_gained=self.xp_gained,
            levelled_up=self.levelled_up,
            new_level=self.new_level,
        ))

    def _flush_stats(self):
        bc = self.battle_controller
        save_system.update_stats(self.save_data, damage=bc.damage_dealt,
                                 turns=bc.turns_taken, abilities=bc.abilities_used)
        if self.player_party:
            self.save_data["player_hp"]     = self.player_party[0].health
            self.save_data["player_max_hp"] = self.player_party[0].max_health

    def _run_enemy_turn(self):
        from systems.ai import BasicAI
        ai = BasicAI()
        for enemy in self.enemy_party:
            if not enemy.is_alive(): continue
            ability, target = ai.choose_action(enemy, self.player_party)
            if ability and target:
                # Double-check: never let enemy target itself or another enemy
                if target not in self.player_party:
                    continue
                self.battle_controller.perform_ability(enemy, ability, target)
                self.assets.play_sound("attack")
        for creature in self.player_party + self.enemy_party:
            for ability in creature.abilities:
                ability.reduce_cooldown()
        # Tick status effects for all creatures at end of full round
        for creature in self.player_party + self.enemy_party:
            creature.update_status_effects()
        self.state = STATE_PLAYER_TURN
        self._set_message("Your turn! Choose an ability.")

    def _set_message(self, text):
        self.message      = text
        self.message_timer = 200

    # ─────────────────────────────────────────────────────────────────────────
    # Drawing
    # ─────────────────────────────────────────────────────────────────────────

    def draw(self, screen):
        if self.state == STATE_BOSS_INTRO:
            self._draw_boss_intro(screen)
            return

        ox, oy = self.shake_offset
        sw, sh = self.sw, self.sh

        bg = self.assets.get_image(self.bg_key)
        if bg: screen.blit(bg, (ox,oy))
        else:  screen.fill((20,20,40))

        # Boss phase flash overlay (after bg, before sprites)
        if self.is_boss_fight and self.boss_screen_flash > 0:
            flash_col = (180, 30, 30) if self.boss_phase == 2 else (180, 0, 80)
            flash_a   = int(110 * self.boss_screen_flash / 30)
            fl = pygame.Surface((sw, sh), pygame.SRCALPHA)
            fl.fill((*flash_col, flash_a))
            screen.blit(fl, (0, 0))

        sprite_y = int(sh * 0.32)
        for i, c in enumerate(self.player_party):
            bx, by = self.idle.get_offset(c)
            self._draw_combatant(screen, c, int(sw*0.10)+i*180, sprite_y, ox+bx, oy+by, flip=False)
        for i, e in enumerate(self.enemy_party):
            bx, by = self.idle.get_offset(e)
            self._draw_combatant(screen, e, int(sw*0.68)-i*220, sprite_y, ox+bx, oy+by, flip=True)

        self.vfx.draw(screen)
        self._draw_ability_bar(screen)
        self._draw_potion_button(screen)
        self._draw_elixir_button(screen)
        self._draw_shield_button(screen)
        self._draw_power_button(screen)
        self._draw_turn_indicator(screen)
        if self.is_boss_fight:
            self._draw_boss_phase_banner(screen)
        self._draw_message(screen)
        if self.matchup_timer > 0: self._draw_matchup(screen)
        if self.potion_timer  > 0: self._draw_potion_msg(screen)
        if self.paused:            self._draw_pause_overlay(screen)

        # HUD — gold, potions, elixirs, shield charges, power shards
        font_small = self.assets.get_font("small")
        if font_small:
            gold    = self.save_data.get("gold", 0)
            pots    = self.save_data.get("potions", 0)
            elixirs = self.save_data.get("elixirs", 0)
            shields = self.save_data.get("shield_charges", 0)
            powers  = self.save_data.get("power_shards", 0)
            hud_x   = sw - 160
            hud_y   = 12
            items   = [
                (f"{gold}g",                 (255, 200,  50)),
                (f"Potion x{pots}",          (100, 220, 100)),
            ]
            if elixirs > 0:
                items.append((f"Elixir x{elixirs}",  (200, 100, 255)))
            if shields > 0:
                items.append((f"Shield x{shields}",  ( 80, 140, 255)))
            if powers > 0:
                items.append((f"Power  x{powers}",   (255, 160,  40)))
            lh = int(sh / 54)
            for j, (txt, col) in enumerate(items):
                s = font_small.render(txt, True, col)
                screen.blit(s, (sw - s.get_width() - 16, hud_y + j * int(lh * 1.6)))

    def _sprite_size(self, creature):
        if is_boss(creature):
            return BOSS_SPRITE_SIZE
        # Scale enemies up by tier, scale player up by evolution stage
        tier = getattr(creature, "battle_tier", 1)
        # Check if it's a player creature (has no battle_tier attr natively)
        from entities.enemy import Enemy as _Enemy
        if not isinstance(creature, _Enemy):
            # Player: size grows with evolution stage stored on save_data
            stage = self.save_data.get("evolution_stage", 0) if self.save_data else 0
            base  = NORMAL_SPRITE_SIZE[0]
            size  = base + stage * 18      # +18px per evo stage
            return (size, size)
        else:
            base = NORMAL_SPRITE_SIZE[0]
            size = base + (tier - 1) * 22  # +22px per tier
            return (size, size)

    def _draw_combatant(self, screen, creature, x, y, ox, oy, flip=False):
        font_small = self.assets.get_font("small")
        sw_s, sh_s = self._sprite_size(creature)
        dx, dy     = x + ox, y + oy
        sprite     = self.assets.get_image(creature.image_path) if creature.image_path else None

        if sprite:
            img = pygame.transform.scale(sprite, (sw_s, sh_s))
            if flip: img = pygame.transform.flip(img, True, False)
            if not creature.is_alive(): img = img.copy(); img.set_alpha(55)
            screen.blit(img, (dx, dy))
        else:
            col = (80,80,80) if not creature.is_alive() else (100,200,100) if not flip else (200,80,80)
            pygame.draw.rect(screen, col, (dx, dy, sw_s, sh_s))

        elem = getattr(creature, "element", None)
        if elem and creature.is_alive():
            ec   = TYPE_COLOURS.get(elem, (180,180,180))
            glow = pygame.Surface((sw_s, 8), pygame.SRCALPHA)
            glow.fill((*ec, 80))
            screen.blit(glow, (dx, dy + sh_s - 4))

        if font_small:
            col    = (255,200,50) if is_boss(creature) else (255,255,255)
            # Scale name to fit sprite width
            shadow = font_small.render(creature.name, True, (0,0,0))
            label  = font_small.render(creature.name, True, col)
            max_nw = sw_s + 20
            if label.get_width() > max_nw:
                sc     = max_nw / label.get_width()
                label  = pygame.transform.scale(label,  (int(label.get_width()*sc),  int(label.get_height()*sc)))
                shadow = pygame.transform.scale(shadow, (label.get_width(), label.get_height()))
            lx = dx + sw_s//2 - label.get_width()//2
            screen.blit(shadow, (lx+1, dy-96))
            screen.blit(label,  (lx,   dy-97))

        # HP bar — clear gap below name
        self._draw_hp_bar(screen, creature, dx-10, dy-60, sw_s+20)

    def _draw_hp_bar(self, screen, creature, x, y, width=140):
        font_small = self.assets.get_font("small")
        ratio      = max(0.0, creature.health/creature.max_health)
        h          = 12
        fill_col   = (50,210,50) if ratio>0.5 else (230,195,0) if ratio>0.25 else (220,50,50)
        pygame.draw.rect(screen, (40,40,40),   (x,y,width,h), border_radius=5)
        if ratio>0: pygame.draw.rect(screen, fill_col, (x,y,int(width*ratio),h), border_radius=5)
        pygame.draw.rect(screen, (160,160,160),(x,y,width,h), 1, border_radius=5)
        if font_small:
            hp_str = f"{max(0,creature.health)}/{creature.max_health}"
            sh_t   = font_small.render(hp_str, True, (0,0,0))
            lb     = font_small.render(hp_str, True, (255,255,255))
            screen.blit(sh_t, (x+1, y-16))
            screen.blit(lb,   (x,   y-16))

    def _ability_slot_rect(self, idx):
        sw, sh  = self.sw, self.sh
        slot_w  = int(sw * 0.10)
        slot_h  = int(sh * 0.09)
        gap     = int(sw * 0.010)
        bar_y   = int(sh * 0.81)
        start_x = int(sw * 0.03)
        return pygame.Rect(start_x + idx*(slot_w+gap), bar_y, slot_w, slot_h)

    def _item_rect(self, slot):
        """Single row of 4 item buttons, right-anchored inside the panel. slot=0..3"""
        sw, sh  = self.sw, self.sh
        w       = int(sw * 0.085)
        h       = int(sh * 0.085)
        gap     = int(sw * 0.008)
        right   = sw - int(sw * 0.015)
        y       = int(sh * 0.885)   # centred inside panel (0.78..1.0)
        x       = right - (4 - slot) * (w + gap)
        return pygame.Rect(x, y, w, h)

    def _potion_rect(self):  return self._item_rect(0)
    def _elixir_rect(self):  return self._item_rect(1)
    def _shield_rect(self):  return self._item_rect(2)
    def _power_rect(self):   return self._item_rect(3)

    def _ability_slot_at(self, pos):
        if not self.player_party: return None
        for idx in range(len(self.player_party[0].abilities)):
            if self._ability_slot_rect(idx).collidepoint(pos):
                return idx
        return None

    def _draw_ability_bar(self, screen):
        if not self.player_party: return
        player     = self.player_party[0]
        font_small = self.assets.get_font("small")
        sh         = self.sh

        panel = pygame.Surface((self.sw, int(sh*0.22)), pygame.SRCALPHA)
        panel.fill((0,0,0,170))
        screen.blit(panel, (0, int(sh*0.78)))

        for idx, ability in enumerate(player.abilities):
            rect    = self._ability_slot_rect(idx)
            ready   = ability.is_ready()
            hovered = (self.hovered_ability == idx)
            my_turn = (self.state == STATE_PLAYER_TURN and not self.paused)
            special = (ability.cooldown >= 5)
            elem    = getattr(ability, "element", None)
            ecol    = TYPE_COLOURS.get(elem, (180,180,180))

            if not ready or not my_turn:
                bg_col, brd_col = (20,20,30), (60,60,70)
            elif hovered:
                bg_col  = tuple(min(255,c+40) for c in ecol[:3])
                brd_col = (255,255,255)
            else:
                bg_col  = tuple(c//3 for c in ecol[:3])
                brd_col = ecol

            pygame.draw.rect(screen, bg_col,  rect, border_radius=8)
            pygame.draw.rect(screen, brd_col, rect, 2, border_radius=8)
            if special and ready and my_turn:
                sh2 = pygame.Surface((rect.w,4), pygame.SRCALPHA)
                sh2.fill((255,200,50,180))
                screen.blit(sh2, (rect.x, rect.y))

            if font_small:
                screen.blit(font_small.render(f"[{idx+1}]", True, (140,140,160)), (rect.x+5, rect.y+4))
                text_col = (255,210,80) if (special and ready and my_turn) else \
                           (255,255,255) if (ready and my_turn) else (75,75,75)
                ab_name = self.assets.render_fitted("small", ability.name, text_col, rect.w - 10)
                if ab_name:
                    screen.blit(ab_name, (rect.x + 5, rect.y + rect.height//2 - ab_name.get_height()//2))
                lh_b = int(self.sh / 54)
                if not ready:
                    cd_s = self.assets.render_fitted("small", f"CD:{ability.current_cooldown}", (200,70,70), rect.w - 10)
                    if cd_s: screen.blit(cd_s, (rect.x+5, rect.bottom - int(lh_b * 1.4)))
                elif my_turn:
                    tag = "SPECIAL" if special else "READY"
                    tc  = (255,180,0) if special else (80,220,80)
                    tg_s = self.assets.render_fitted("small", tag, tc, rect.w - 10)
                    if tg_s: screen.blit(tg_s, (rect.x+5, rect.bottom - int(lh_b * 1.4)))
                if elem:
                    el = font_small.render(elem.upper(), True, (*ecol[:3],))
                    screen.blit(el, (rect.right - el.get_width() - 4, rect.y+4))

    def _draw_potion_button(self, screen):
        font_small = self.assets.get_font("small")
        rect       = self._potion_rect()
        pots       = self.save_data.get("potions", 0)
        has        = pots > 0
        my_turn    = (self.state == STATE_PLAYER_TURN and not self.paused)

        bc  = (30,70,30) if (has and my_turn) else (30,30,30)
        brd = (80,200,80) if (has and my_turn) else (60,60,60)
        pygame.draw.rect(screen, bc,  rect, border_radius=8)
        pygame.draw.rect(screen, brd, rect, 2, border_radius=8)
        if font_small:
            screen.blit(font_small.render("[H]", True, (140,140,160)), (rect.x+5, rect.y+4))
            screen.blit(font_small.render("Potion", True, (180,240,180) if has else (80,80,80)),
                        (rect.x+5, rect.y+rect.h//2-5))
            screen.blit(font_small.render(f"x{pots}", True, (120,220,120) if has else (60,60,60)),
                        (rect.x+5, rect.bottom - int(self.sh / 38)))

    def _draw_elixir_button(self, screen):
        font_small = self.assets.get_font("small")
        rect       = self._elixir_rect()
        elixirs    = self.save_data.get("elixirs", 0)
        has        = elixirs > 0
        my_turn    = (self.state == STATE_PLAYER_TURN and not self.paused)

        bc  = (55, 20, 75) if (has and my_turn) else (30, 30, 30)
        brd = (180, 80, 255) if (has and my_turn) else (60, 60, 60)
        pygame.draw.rect(screen, bc,  rect, border_radius=8)
        pygame.draw.rect(screen, brd, rect, 2, border_radius=8)
        if font_small:
            screen.blit(font_small.render("[J]",    True, (140,100,180)), (rect.x+5, rect.y+4))
            screen.blit(font_small.render("Elixir", True, (210,160,255) if has else (80,80,80)),
                        (rect.x+5, rect.y+rect.h//2-5))
            screen.blit(font_small.render(f"x{elixirs}", True, (190,130,255) if has else (60,60,60)),
                        (rect.x+5, rect.bottom - int(self.sh / 38)))

    def _draw_shield_button(self, screen):
        font_small = self.assets.get_font("small")
        rect       = self._shield_rect()
        charges    = self.save_data.get("shield_charges", 0)
        has        = charges > 0
        my_turn    = (self.state == STATE_PLAYER_TURN and not self.paused)
        bc  = (20, 40, 80) if (has and my_turn) else (30, 30, 30)
        brd = (80, 140, 255) if (has and my_turn) else (60, 60, 60)
        pygame.draw.rect(screen, bc,  rect, border_radius=8)
        pygame.draw.rect(screen, brd, rect, 2, border_radius=8)
        if font_small:
            screen.blit(font_small.render("[S]",     True, (100, 140, 200)), (rect.x+5, rect.y+4))
            screen.blit(font_small.render("Shield",  True, (140,200,255) if has else (80,80,80)),
                        (rect.x+5, rect.y+rect.h//2-5))
            screen.blit(font_small.render(f"x{charges}", True, (120,180,255) if has else (60,60,60)),
                        (rect.x+5, rect.bottom - int(self.sh / 38)))

    def _draw_power_button(self, screen):
        font_small = self.assets.get_font("small")
        rect       = self._power_rect()
        shards     = self.save_data.get("power_shards", 0)
        has        = shards > 0
        my_turn    = (self.state == STATE_PLAYER_TURN and not self.paused)
        bc  = (70, 40, 10) if (has and my_turn) else (30, 30, 30)
        brd = (255, 160, 40) if (has and my_turn) else (60, 60, 60)
        pygame.draw.rect(screen, bc,  rect, border_radius=8)
        pygame.draw.rect(screen, brd, rect, 2, border_radius=8)
        if font_small:
            screen.blit(font_small.render("[D]",    True, (200, 140, 60)), (rect.x+5, rect.y+4))
            screen.blit(font_small.render("Power",  True, (255,180,80) if has else (80,80,80)),
                        (rect.x+5, rect.y+rect.h//2-5))
            screen.blit(font_small.render(f"x{shards}", True, (255,160,60) if has else (60,60,60)),
                        (rect.x+5, rect.bottom - int(self.sh / 38)))

    def _draw_turn_indicator(self, screen):
        font_small = self.assets.get_font("small")
        if not font_small: return
        if   self.paused:                    text, col = "PAUSED",          (255,200,50)
        elif self.state==STATE_PLAYER_TURN:  text, col = ">> YOUR TURN <<", (100,220,100)
        elif self.state==STATE_ENEMY_TURN:   text, col = "ENEMY TURN...",   (220,100,100)
        else:                                text, col = "...",              (180,180,180)
        surf   = font_small.render(text, True, col)
        shadow = font_small.render(text, True, (0,0,0))
        x = self.sw//2 - surf.get_width()//2
        y = int(self.sh*0.78)
        screen.blit(shadow, (x+1,y+1)); screen.blit(surf, (x,y))

    def _draw_message(self, screen):
        font_small = self.assets.get_font("small")
        if not font_small or not self.message: return
        surf = self.assets.render_fitted("small", self.message, (255,230,80), self.sw - 20)
        if not surf: return
        shadow = self.assets.render_fitted("small", self.message, (0,0,0), self.sw - 20)
        x = self.sw//2 - surf.get_width()//2
        y = int(self.sh*0.75)
        if shadow: screen.blit(shadow, (x+1,y+1))
        screen.blit(surf, (x,y))

    def _draw_matchup(self, screen):
        font_medium = self.assets.get_font("medium")
        if not font_medium: return
        alpha  = min(255, self.matchup_timer*4)
        surf   = font_medium.render(self.matchup_text, True, self.matchup_colour)
        shadow = font_medium.render(self.matchup_text, True, (0,0,0))
        surf.set_alpha(alpha); shadow.set_alpha(alpha//2)
        x = self.sw//2 - surf.get_width()//2
        y = int(self.sh*0.70)
        screen.blit(shadow, (x+2,y+2)); screen.blit(surf, (x,y))

    def _draw_potion_msg(self, screen):
        font_small = self.assets.get_font("small")
        if not font_small: return
        col  = (100,220,100) if "Used" in self.potion_msg else (220,80,80)
        surf = font_small.render(self.potion_msg, True, col)
        x    = self.sw//2 - surf.get_width()//2
        screen.blit(surf, (x, int(self.sh*0.71)))

    def _draw_pause_overlay(self, screen):
        ov = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        ov.fill((0,0,0,160)); screen.blit(ov, (0,0))
        font_large = self.assets.get_font("large")
        font_small = self.assets.get_font("small")
        cx, cy     = self.sw//2, self.sh//2
        if font_large:
            t = font_large.render("PAUSED", True, (255,220,60))
            screen.blit(t, (cx - t.get_width()//2, cy-80))
        if font_small:
            for i, line in enumerate(["[P]  Resume", "[Q]  Quit to Map"]):
                s = font_small.render(line, True, (200,200,200))
                screen.blit(s, (cx - s.get_width()//2, cy + i*30))

    def _draw_boss_phase_banner(self, screen):
        """Draws enrage/desperate banner + HP phase indicator for boss fights."""
        import math as _m
        sw, sh     = self.sw, self.sh
        font_small  = self.assets.get_font("small")
        font_medium = self.assets.get_font("medium")

        if not self.enemy_party: return
        boss = self.enemy_party[0]
        if not boss.is_alive(): return

        # Phase indicator in top-left corner
        ratio = boss.health / boss.max_health
        if self.boss_phase >= 3:
            phase_col  = (255, 60, 150)
            phase_text = "DESPERATE"
        elif self.boss_phase >= 2:
            phase_col  = (255, 80, 40)
            phase_text = "ENRAGED"
        else:
            return   # phase 1 = no banner

        # Pulsing phase label
        pulse = abs(_m.sin(self.boss_phase_timer * 0.08 + self.timer * 0.05)) * 0.4 + 0.6
        if font_medium:
            ps = font_medium.render(f"⚡ {boss.name}: {phase_text} ⚡", True, phase_col)
            if ps.get_width() > sw - 20:
                sc = (sw - 20) / ps.get_width()
                ps = pygame.transform.scale(ps, (int(ps.get_width()*sc), int(ps.get_height()*sc)))
            ps.set_alpha(int(220 * pulse))
            screen.blit(ps, (sw // 2 - ps.get_width() // 2, int(sh * 0.06)))

        # Show phase transition message
        if self.boss_phase_timer > 0 and font_medium:
            fade = min(1.0, self.boss_phase_timer / 50)
            ms = font_medium.render(self.boss_phase_msg, True, phase_col)
            ms.set_alpha(int(255 * fade))
            screen.blit(ms, (sw // 2 - ms.get_width() // 2, int(sh * 0.14)))

    def _draw_boss_intro(self, screen):
        sw, sh = self.sw, self.sh
        cx     = sw//2
        bg     = self.assets.get_image(self.bg_key)
        if bg:
            dark = bg.copy(); dark.set_alpha(60); screen.blit(dark, (0,0))
        else:
            screen.fill((10,5,20))

        ov = pygame.Surface((sw, sh), pygame.SRCALPHA)
        ov.fill((0,0,0,190)); screen.blit(ov, (0,0))

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        boss = self.enemy_party[0] if self.enemy_party else None

        # Boss sprite — large for cinematic impact
        if boss:
            sprite = self.assets.get_image(boss.image_path)
            if sprite:
                scaled = pygame.transform.scale(sprite, (300, 300))
                screen.blit(scaled, (cx - 150, int(sh * 0.06)))
            if font_large:
                t    = font_large.render(boss.name, True, (255, 140, 30))
                sh_t = font_large.render(boss.name, True, (0, 0, 0))
                screen.blit(sh_t, (cx - t.get_width()//2 + 2, int(sh * 0.46) + 2))
                screen.blit(t,    (cx - t.get_width()//2,     int(sh * 0.46)))

        # Taunt
        if self.taunts and self.taunt_index < len(self.taunts):
            taunt = self.taunts[self.taunt_index]
            if font_medium:
                fade  = min(1.0, self.taunt_timer / 30)
                surf  = font_medium.render(taunt, True, (220,200,160))
                if surf.get_width() > sw - 40:
                    sc   = (sw - 40) / surf.get_width()
                    surf = pygame.transform.scale(surf, (int(surf.get_width()*sc), int(surf.get_height()*sc)))
                surf.set_alpha(int(255*fade))
                screen.blit(surf, (cx - surf.get_width()//2, int(sh*0.60)))

        if self.taunt_timer > 30 and font_small:
            h = font_small.render("Press any key to fight", True, (100,100,120))
            screen.blit(h, (cx - h.get_width()//2, int(sh*0.90)))