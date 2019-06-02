import sys
import itertools

import Utils
from ArcadeView import ArcadeView
from RecordSaver import RecordSaver
from SokobanGameEngine import SokobanGameEngine
from map_generator.MapGenerator import generate_map
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum

player_position = []
game_map = Utils.generate_example_map()

LEVEL = "VERY_SIMPLE_level_1"

if __name__ == "__main__":
    # input_moves = Utils.get_moves_from_record_file("manual_games\\simple_level_3_2019-06-02_11-03-31.txt")
    input_moves, rotations = Utils.get_input_moves_list_starting_with("learned_games", LEVEL)
    print(input_moves)
    print("Num of input moves: ", len(input_moves))
    print("Rotations: ", rotations)
    # input_moves = Utils.get_example_moves()
    # input_moves = None

    RecordSaver.record_path = Utils.get_record_path(sys.argv)
    game_map = Utils.read_map_from_file_path("levels", LEVEL)
    Utils.set_width_and_height(game_map)

    arcade_view = ArcadeView(game_map)

    sokobanGameEngine = SokobanGameEngine(game_map, arcade_view, input_moves, rotations)

    # generate_map()

    # Permutacje od 12 dzialaja bardzo wolno
    # l = set(list(itertools.permutations(range(1, 11))))
    # print(l)

    # test_per = [MapGeneratorPlayerActionEnum.PULL_CHEST, MapGeneratorPlayerActionEnum.PULL_CHEST,
    #             MapGeneratorPlayerActionEnum.CHANGE_SIDE, MapGeneratorPlayerActionEnum.CHANGE_SIDE]
    # l = set(list(itertools.permutations(test_per)))
    # [print(per) for per in l]
    # print(l)

# First move probably should be pull chest
