import arcade

import Constants as cs
import BlockType
from SobokanGame import SobokanGame
import Utils

player_position = []
game_map = Utils.generate_example_map()


# def main():
#
#     arcade.finish_render()
#     arcade.run()


if __name__ == "__main__":
    print('Hello')
    window = SobokanGame(cs.WINDOW_WIDTH, cs.WINDOW_HEIGHT, cs.TITLE, game_map)
    arcade.run()