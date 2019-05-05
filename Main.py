import sys

import Utils
from RecordSaver import RecordSaver
from SobokanGameEngine import SobokanGameEngine

player_position = []
game_map = Utils.generate_example_map()

if __name__ == "__main__":
    input_moves = Utils.get_moves_from_record_file("simple_level_2_2019-05-05_18-57-32.txt")
    # input_moves = Utils.get_example_moves()
    # input_moves = None

    level_path = Utils.get_level_path(sys.argv)
    RecordSaver.record_path = Utils.get_record_path(sys.argv)
    game_map = Utils.read_map_from_file_path(level_path)
    Utils.set_width_and_height(game_map)
    sobokanGameEngine = SobokanGameEngine(game_map,  input_moves)
    # arcade.run()
