import arcade
import sys

from RecordSaver import RecordSaver
import SobParams as cs
import Utils
from SobokanGame import SobokanGame

player_position = []
game_map = Utils.generate_example_map()

if __name__ == "__main__":
    level_path = Utils.get_level_path(sys.argv)
    RecordSaver.level_path = level_path
    game_map = Utils.read_map_from_file_path(level_path)
    Utils.set_width_and_height(game_map)
    window = SobokanGame(cs.WINDOW_WIDTH, cs.WINDOW_HEIGHT, cs.TITLE, game_map)
    arcade.run()



