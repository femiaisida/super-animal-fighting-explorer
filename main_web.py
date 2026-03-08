import asyncio
import traceback
import pygame

async def main():
    try:
        from game import Game
        from scenes.loading_scene import LoadingScene
        game = Game(web_mode=True)
        game.scene_manager.switch(LoadingScene(game.scene_manager, game.assets))
        while game.running:
            dt = game.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.running = False
                game.scene_manager.handle_event(event)
            game.scene_manager.update(dt)
            game.scene_manager.draw(game.screen)
            pygame.display.flip()
            await asyncio.sleep(0)
        pygame.quit()
    except Exception as e:
        print("GAME CRASH:", e)
        traceback.print_exc()
        # Draw error to screen so we can see it
        try:
            screen = pygame.display.get_surface()
            if screen:
                pygame.font.init()
                f = pygame.font.SysFont("monospace", 14)
                screen.fill((20, 0, 0))
                lines = traceback.format_exc().split("\n")
                for i, line in enumerate(lines[-20:]):
                    surf = f.render(line[:80], True, (255, 100, 100))
                    screen.blit(surf, (10, 10 + i * 18))
                pygame.display.flip()
        except Exception:
            pass
        while True:
            await asyncio.sleep(1)

asyncio.run(main())
