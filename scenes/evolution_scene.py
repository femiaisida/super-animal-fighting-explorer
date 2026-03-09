import pygame
import math
from core.scene_manager import Scene
from systems.story import get_evolution_text


class EvolutionScene(Scene):
    """
    Shown after a boss kill when the player has not yet evolved.
    Plays through story text, then confirms evolution.
    """

    def __init__(self, manager, assets, character, save_data, player_party, on_complete):
        super().__init__(manager)
        self.assets       = assets
        self.character    = character
        self.save_data    = save_data
        self.player_party = player_party
        self.on_complete  = on_complete   # callable(save_data, player_party)

        self.sw = assets.screen_w
        self.sh = assets.screen_h

        self.assets.stop_music()
        self.assets.play_music("evolution")   # plays if evolution.mp3/ogg exists, silent if not

        # Stage being evolved TO (current stage + 1)
        target_stage  = self.save_data.get("evolution_stage", 0) + 1
        self.evo_data = get_evolution_text(character, target_stage)

        # Phase: "before" → "evolving" → "after" → "done"
        self.phase      = "before"
        self.phase_timer = 0
        self.fade_in    = 0.0
        self.anim_time  = 0.0
        self.confirmed  = False

        # Particle burst state
        self.particles  = []

    def handle_event(self, event):
        if self.phase_timer < 40:
            return
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.assets.play_sound("click")
            if self.phase == "before":
                self._start_evolution()
            elif self.phase == "after":
                self._finish()

    def _start_evolution(self):
        self.phase       = "evolving"
        self.phase_timer = 0
        self.fade_in     = 0.0
        self.assets.play_sound("evolution")
        self._spawn_particles()

    def _spawn_particles(self):
        import random
        cx, cy = self.sw // 2, self.sh // 2
        for _ in range(60):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x": float(cx), "y": float(cy),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(40, 80),
                "age": 0,
                "col": random.choice([
                    (255, 200, 50), (255, 120, 40), (180, 100, 255), (255, 255, 255)
                ]),
            })

    def _finish(self):
        import systems.save_system as ss
        from data.creatures import make_player, CHARACTER_DATA
        # Advance to next stage
        new_stage = self.save_data.get("evolution_stage", 0) + 1
        max_stage = len(CHARACTER_DATA.get(self.character, CHARACTER_DATA["void"])["stages"]) - 1
        new_stage = min(new_stage, max_stage)
        self.save_data["evolution_stage"]  = new_stage
        self.save_data["evolved"]          = new_stage > 0
        self.save_data["pending_evolution"] = False

        new_player = make_player(self.character, stage=new_stage)
        # Apply level HP bonus
        hp_bonus = self.save_data.get("level_hp_bonus", 0)
        new_player.max_health += hp_bonus
        new_player.health = new_player.max_health
        self.save_data["player_hp"]     = new_player.max_health
        self.save_data["player_max_hp"] = new_player.max_health
        ss.save(self.save_data)
        self.on_complete(self.save_data, [new_player])

    def update(self, dt):
        self.phase_timer += 1
        self.anim_time   += dt
        self.fade_in      = min(1.0, self.fade_in + dt * 1.5)

        # Auto-advance "evolving" phase after animation
        if self.phase == "evolving" and self.phase_timer > 80:
            self.phase       = "after"
            self.phase_timer = 0
            self.fade_in     = 0.0

        # Update particles
        for p in self.particles:
            p["x"]   += p["vx"]
            p["y"]   += p["vy"]
            p["vy"]  += 0.15
            p["age"] += 1
        self.particles = [p for p in self.particles if p["age"] < p["life"]]

    def draw(self, screen):
        sw, sh = self.sw, self.sh
        cx, cy = sw // 2, sh // 2
        alpha  = int(255 * self.fade_in)

        font_large  = self.assets.get_font("large")
        font_medium = self.assets.get_font("medium")
        font_small  = self.assets.get_font("small")

        screen.fill((5, 0, 20))

        # Pulsing circle glow
        pulse = abs(math.sin(self.anim_time * 2)) * 0.5 + 0.5
        for r in range(200, 0, -20):
            a = int(30 * pulse * (1 - r / 200))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (180, 100, 255, a), (r, r), r)
            screen.blit(s, (cx - r, cy - r))

        # Particles
        for p in self.particles:
            a = int(255 * (1 - p["age"] / p["life"]))
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["col"][:3], a), (3, 3), 3)
            screen.blit(s, (int(p["x"]) - 3, int(p["y"]) - 3))

        if self.phase == "before":
            self._draw_lines(screen, cx, cy, alpha,
                             "A Change Approaches...", self.evo_data.get("before", []),
                             (180, 140, 255), font_large, font_medium, font_small)

        elif self.phase == "evolving":
            # Bright flash
            flash_a = max(0, 255 - self.phase_timer * 5)
            if flash_a > 0:
                fl = pygame.Surface((sw, sh), pygame.SRCALPHA)
                fl.fill((255, 255, 255, flash_a))
                screen.blit(fl, (0, 0))
            if font_large:
                t = font_large.render("EVOLVING!", True, (255, 200, 50))
                t.set_alpha(min(255, self.phase_timer * 6))
                screen.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

        elif self.phase == "after":
            from data.creatures import get_stage_data
            new_stage    = self.save_data.get("evolution_stage", 0) + 1
            stage_info   = get_stage_data(self.character, new_stage)
            evolved_name = stage_info["name"]
            self._draw_lines(screen, cx, cy, alpha,
                             f"You are now {evolved_name}!", self.evo_data.get("after", []),
                             (255, 200, 50), font_large, font_medium, font_small)
            # Show evolved sprite if available
            sprite = self.assets.get_image(stage_info["img"]) or \
                     self.assets.get_image(self.character)
            if sprite:
                scaled = pygame.transform.scale(sprite, (160, 160))
                scaled.set_alpha(alpha)
                screen.blit(scaled, (cx - 80, int(sh * 0.55)))

        if self.phase_timer > 40 and font_small:
            hint_text = "Press any key to evolve" if self.phase == "before" else \
                        "Press any key to continue" if self.phase == "after" else ""
            if hint_text:
                h = font_small.render(hint_text, True, (100, 100, 120))
                screen.blit(h, (cx - h.get_width() // 2, int(sh * 0.93)))

    def _draw_lines(self, screen, cx, cy, alpha, title, lines, col,
                    font_large, font_medium, font_small):
        sh = self.sh
        if font_large:
            t  = font_large.render(title, True, col)
            sh_t = font_large.render(title, True, (0, 0, 0))
            t.set_alpha(alpha)
            sh_t.set_alpha(alpha // 2)
            tx = cx - t.get_width() // 2
            screen.blit(sh_t, (tx + 2, int(sh * 0.18) + 2))
            screen.blit(t,    (tx,     int(sh * 0.18)))

        if font_medium:
            ly  = int(sh * 0.35)
            gap = int(sh * 0.07)
            for i, line in enumerate(lines):
                da = max(0, min(255, int(alpha - i * 20)))
                s  = font_medium.render(line, True, (210, 210, 210))
                sh_s = font_medium.render(line, True, (0, 0, 0))
                s.set_alpha(da)
                sh_s.set_alpha(da // 2)
                lx = cx - s.get_width() // 2
                screen.blit(sh_s, (lx + 1, ly + 1))
                screen.blit(s,    (lx,     ly))
                ly += gap