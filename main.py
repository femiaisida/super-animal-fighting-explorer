from game import Game
from scenes.loading_scene import LoadingScene


def create_game():
    game = Game()
    game.scene_manager.switch(LoadingScene(game.scene_manager, game.assets))
    return game


if __name__ == "__main__":
    game = create_game()
    game.run()
