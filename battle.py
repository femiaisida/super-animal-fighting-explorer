import random
import pygame


# Visual layout constants to avoid magic numbers scattered throughout.
SPRITE_SIZE = (180, 180)
LEFT_SPRITE_POS = (120, 180)
RIGHT_SPRITE_POS = (724, 180)
NAME_OFFSET_Y = -50
POPUP_DURATION = 0.9  # seconds


class Button:
    def __init__(self, rect, label, font):
        self.rect = rect
        self.label = label
        self.font = font

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, screen, hovered=False, disabled=False):
        bg = (70, 70, 70) if not hovered else (90, 90, 90)
        if disabled:
            bg = (50, 50, 50)
        pygame.draw.rect(screen, bg, self.rect, border_radius=6)
        pygame.draw.rect(screen, (20, 20, 20), self.rect, 2, border_radius=6)
        text = self.font.render(self.label, True, (230, 230, 230))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Battle:
    """
    Handles battle logic and rendering.
    Does NOT control the game state machine (main.py owns that).
    Returns outcome via self.outcome: None, "WIN", or "LOSE".
    """

    def __init__(
        self,
        player,
        enemy,
        font,
        attack_sound=None,
        click_sound=None,
        small_font=None,
        screen_size=(1024, 768),
    ):
        self.player = player
        self.enemies = enemy if isinstance(enemy, list) else [enemy]
        self.font = font
        self.small_font = small_font or font
        self.attack_sound = attack_sound
        self.click_sound = click_sound
        self.outcome = None
        self.target_index = 0
        self.message = self._build_intro_message()
        self.popups = []  # list of dicts: {text, pos, color, time_left}

        self.screen_width, self.screen_height = screen_size
        self._compute_layout()
        self.player_sprite = self._prepare_sprite(self.player.sprite)
        self.enemy_sprites = [self._prepare_sprite(enemy.sprite) for enemy in self.enemies]

        self.attack_btn = Button(self.attack_rect, "ATTACK", font)
        self.special_btn = Button(self.special_rect, "SPECIAL", font)

    def _build_intro_message(self):
        names = [enemy.element for enemy in self.enemies]
        if not names:
            return "An eerie silence fills the battlefield..."
        if len(names) == 1:
            return f"A wild {names[0]} creature appears!"
        return f"{len(names)} enemies appear!"

    def _prepare_sprite(self, sprite):
        return pygame.transform.smoothscale(sprite, self.sprite_size)

    def _compute_layout(self):
        scale = min(self.screen_width / 1024, self.screen_height / 768)
        sprite = int(180 * scale)
        self.sprite_size = (sprite, sprite)
        self.left_pos = (int(120 * scale), int(self.screen_height * 0.23))
        self.right_pos = (self.screen_width - int(120 * scale) - sprite, int(self.screen_height * 0.23))
        self.enemy_positions = []
        self.name_offset_y = int(NAME_OFFSET_Y * scale)
        self.health_bar_offset_y = int(-25 * scale)
        self.health_bar_size = (int(280 * scale), int(16 * scale))
        self.message_pos = (int(140 * scale), int(self.screen_height * 0.65))
        self.controls_pos = (int(140 * scale), int(self.screen_height * 0.72))
        button_y = int(self.screen_height * 0.80)
        button_w = int(220 * scale)
        button_h = int(56 * scale)
        self.attack_rect = pygame.Rect(int(self.screen_width * 0.35) - button_w // 2, button_y, button_w, button_h)
        self.special_rect = pygame.Rect(int(self.screen_width * 0.65) - button_w // 2, button_y, button_w, button_h)
        self._recompute_enemy_positions()

    def _recompute_enemy_positions(self):
        self.enemy_positions.clear()
        alive = self._alive_enemies()
        count = max(1, len(alive))
        pad = int(24 * min(self.screen_width / 1024, self.screen_height / 768))
        total_w = count * self.sprite_size[0] + (count - 1) * pad
        start_x = self.screen_width - int(120 * min(self.screen_width / 1024, self.screen_height / 768)) - total_w
        y = int(self.screen_height * 0.23)
        for i in range(count):
            self.enemy_positions.append((start_x + i * (self.sprite_size[0] + pad), y))

    def _add_popup(self, text, pos, color):
        self.popups.append(
            {
                "text": text,
                "pos": list(pos),
                "color": color,
                "time_left": POPUP_DURATION,
            }
        )

    def _alive_enemies(self):
        return [enemy for enemy in self.enemies if not enemy.is_defeated()]

    def _alive_indices(self):
        return [idx for idx, enemy in enumerate(self.enemies) if not enemy.is_defeated()]

    def _get_target(self):
        alive = self._alive_enemies()
        if not alive:
            return None, None
        self.target_index = max(0, min(self.target_index, len(alive) - 1))
        return alive[self.target_index], self.target_index

    def _enemy_at_pos(self, mouse_pos):
        alive = self._alive_enemies()
        for idx, (enemy, pos) in enumerate(zip(alive, self.enemy_positions)):
            rect = pygame.Rect(pos[0], pos[1], self.sprite_size[0], self.sprite_size[1])
            if rect.collidepoint(mouse_pos):
                return idx
        return None

    def handle_event(self, event):
        if self.outcome is not None:
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                alive = self._alive_enemies()
                if alive:
                    self.target_index = (self.target_index - 1) % len(alive)
                return
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                alive = self._alive_enemies()
                if alive:
                    self.target_index = (self.target_index + 1) % len(alive)
                return
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._play_sound(self.click_sound)
                self._player_attack(use_special=False)
                return
            if event.key in (pygame.K_s, pygame.K_x):
                self._play_sound(self.click_sound)
                if self.player.special_uses > 0:
                    self._player_attack(use_special=True)
                else:
                    self.message = "No special uses left!"
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked = self._enemy_at_pos(event.pos)
            if clicked is not None:
                self.target_index = clicked
                self._play_sound(self.click_sound)
                return

        if self.attack_btn.is_clicked(event):
            self._play_sound(self.click_sound)
            self._player_attack(use_special=False)
        elif self.special_btn.is_clicked(event):
            self._play_sound(self.click_sound)
            if self.player.special_uses > 0:
                self._player_attack(use_special=True)
            else:
                self.message = "No special uses left!"

    def _player_attack(self, use_special):
        if use_special and self.player.special_uses <= 0:
            return

        alive = self._alive_enemies()
        if not alive:
            self.outcome = "WIN"
            self.message = "Enemy defeated!"
            return

        if use_special and len(alive) > 1:
            self.player.special_uses -= 1
            self._play_sound(self.attack_sound)
            total_damage = 0
            for idx, enemy in enumerate(list(alive)):
                damage = self.player.roll_special_damage()
                total_damage += damage
                enemy.take_damage(damage)
                popup_pos = self.enemy_positions[idx]
                self._add_popup(
                    f"-{damage}",
                    (popup_pos[0] + 60, popup_pos[1] - 10),
                    (255, 180, 120),
                )

            if not self._alive_enemies():
                self.outcome = "WIN"
                self.message = "Enemies defeated!"
                return
            self._recompute_enemy_positions()
            self.target_index = max(0, min(self.target_index, len(self._alive_enemies()) - 1))

            counter = random.choice(self._alive_enemies())
            enemy_damage = counter.roll_damage()
            self._play_sound(self.attack_sound)
            self.player.take_damage(enemy_damage)
            self._add_popup(
                f"-{enemy_damage}",
                (self.left_pos[0] + 60, self.left_pos[1] - 10),
                (255, 120, 120),
            )
            self.message = f"Special hit all enemies for {total_damage} total. Enemy hit back for {enemy_damage}."
            if self.player.is_defeated():
                self.outcome = "LOSE"
                self.message = "You have been defeated!"
            return

        target, target_index = self._get_target()
        if target is None:
            self.outcome = "WIN"
            self.message = "Enemy defeated!"
            return

        if use_special:
            damage = self.player.roll_special_damage()
            self.player.special_uses -= 1
        else:
            damage = self.player.roll_damage()

        self._play_sound(self.attack_sound)
        target.take_damage(damage)
        popup_pos = self.enemy_positions[target_index]
        self._add_popup(
            f"-{damage}",
            (popup_pos[0] + 60, popup_pos[1] - 10),
            (255, 180, 120),
        )

        if target.is_defeated():
            if not self._alive_enemies():
                self.outcome = "WIN"
                self.message = "Enemy defeated!"
                return
            self._recompute_enemy_positions()
            self.target_index = max(0, min(self.target_index, len(self._alive_enemies()) - 1))

        # Enemy counterattack
        counter = random.choice(self._alive_enemies())
        enemy_damage = counter.roll_damage()
        self._play_sound(self.attack_sound)
        self.player.take_damage(enemy_damage)
        self._add_popup(
            f"-{enemy_damage}",
            (self.left_pos[0] + 60, self.left_pos[1] - 10),
            (255, 120, 120),
        )

        self.message = f"You dealt {damage}. Enemy hit back for {enemy_damage}."

        if self.player.is_defeated():
            self.outcome = "LOSE"
            self.message = "You have been defeated!"

    def update(self, dt):
        # Update floating damage popups with frame-independent timing.
        for popup in list(self.popups):
            popup["time_left"] -= dt
            popup["pos"][1] -= 20 * dt
            if popup["time_left"] <= 0:
                self.popups.remove(popup)

    def draw(self, screen):
        self._draw_creature(screen, self.player, self.player_sprite, self.left_pos, "PLAYER")
        alive_indices = self._alive_indices()
        alive_enemies = self._alive_enemies()
        for idx, enemy_index in enumerate(alive_indices):
            enemy = alive_enemies[idx]
            sprite = self.enemy_sprites[enemy_index]
            pos = self.enemy_positions[idx]
            label = f"ENEMY {idx + 1}" if len(alive_enemies) > 1 else "ENEMY"
            self._draw_creature(screen, enemy, sprite, pos, label)
            if idx == self.target_index:
                highlight = pygame.Rect(pos[0] - 4, pos[1] - 4, self.sprite_size[0] + 8, self.sprite_size[1] + 8)
                pygame.draw.rect(screen, (255, 210, 120), highlight, 2, border_radius=6)

        mouse_pos = pygame.mouse.get_pos()
        self.attack_btn.draw(screen, hovered=self.attack_btn.is_hovered(mouse_pos))
        self.special_btn.draw(
            screen,
            hovered=self.special_btn.is_hovered(mouse_pos),
            disabled=self.player.special_uses <= 0,
        )

        # Message box
        self._draw_message(screen, self.message)
        self._draw_controls(screen)

        # Popups
        for popup in self.popups:
            text = self.font.render(popup["text"], True, popup["color"])
            screen.blit(text, popup["pos"])

    def _draw_creature(self, screen, creature, sprite, pos, label):
        screen.blit(sprite, pos)
        name = f"{label}: {creature.element.capitalize()}"
        name_surface = self.font.render(name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(midleft=(pos[0], pos[1] + self.name_offset_y))
        screen.blit(name_surface, name_rect)

        bar_x = pos[0]
        bar_y = pos[1] + self.health_bar_offset_y
        self._draw_health_bar(screen, creature, bar_x, bar_y)

    def _draw_health_bar(self, screen, creature, x, y):
        max_health = max(1, creature.max_health)
        current = max(0, creature.current_health)
        ratio = current / max_health

        pygame.draw.rect(screen, (60, 60, 60), (x, y, self.health_bar_size[0], self.health_bar_size[1]))
        pygame.draw.rect(
            screen,
            (180, 60, 60),
            (x, y, int(self.health_bar_size[0] * ratio), self.health_bar_size[1]),
        )
        pygame.draw.rect(screen, (20, 20, 20), (x, y, self.health_bar_size[0], self.health_bar_size[1]), 2)

        hp_text = self.font.render(f"HP: {current} / {max_health}", True, (230, 230, 230))
        screen.blit(hp_text, (x, y + 22))

    def _draw_message(self, screen, text):
        msg_surface = self.font.render(text, True, (240, 240, 240))
        screen.blit(msg_surface, self.message_pos)

    def _draw_controls(self, screen):
        lines = [
            "Controls:",
            "Arrows/A-D: select target  Enter/Space: attack",
            "S/X: special  Click enemy: target",
        ]
        y = self.controls_pos[1]
        for line in lines:
            surface = self.small_font.render(line, True, (220, 220, 220))
            screen.blit(surface, (self.controls_pos[0], y))
            y += surface.get_height() + 4

    def _play_sound(self, sound):
        if sound:
            sound.play()
