import asyncio
import pygame
from game import Game
from scenes.loading_scene import LoadingScene

async def main():
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

asyncio.run(main())
