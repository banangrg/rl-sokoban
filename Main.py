import sys

import arcade

import SobParams as cs
import Utils
from RecordSaver import RecordSaver
from SobokanGameEngine import SobokanGameEngine

player_position = []
game_map = Utils.generate_example_map()

if __name__ == "__main__":
    level_path = Utils.get_level_path(sys.argv)
    RecordSaver.record_path = Utils.get_record_path(sys.argv)
    game_map = Utils.read_map_from_file_path(level_path)
    Utils.set_width_and_height(game_map)
    sobokanGameEngine = SobokanGameEngine(game_map)
    arcade.run()


