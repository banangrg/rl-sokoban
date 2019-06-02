import sys
import itertools

import Utils
from ArcadeView import ArcadeView
from RecordSaver import RecordSaver
from SobokanGameEngine import SobokanGameEngine
from map_generator.MapGenerator import generate_map
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum

player_position = []
game_map = Utils.generate_example_map()

if __name__ == "__main__":
    input_moves = Utils.get_moves_from_record_file("manual_games\\simple_level_3_2019-06-02_11-03-31.txt")
    # input_moves = Utils.get_example_moves()
    # input_moves = None
    #
    # level_path = Utils.get_level_path(sys.argv)
    RecordSaver.record_path = Utils.get_record_path(sys.argv)
    game_map = Utils.read_map_from_file_path("levels\\simple_level_3.txt")
    Utils.set_width_and_height(game_map)

    arcade_view = ArcadeView(game_map)

    # try:
    #     sobokanGameEngine = SobokanGameEngine(game_map, arcade_view, input_moves)
    # except:
    #     pass

    sobokanGameEngine = SobokanGameEngine(game_map, arcade_view, [input_moves, input_moves])
    # sobokanGameEngine = SobokanGameEngine(game_map)

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
