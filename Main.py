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

LEVEL = "MEDIUM_map_8"
# LEVEL = "1\\[7, 7, 1, 18, 0__550_episodes_2019-06-19_21-07-51.281324"
game_map_name_1 = "1\\[7, 7, 1, 18, 0.75, 0.25]_2019-06-19_21-07-51"
results_file_name_1 = "1\\[7, 7, 1, 18, 0__550_episodes_2019-06-19_21-07-51.281324"
game_map_name_2 = "2\\[13, 10, 1, 26, 0.75, 0.25]_2019-06-20_08-26-40"
results_file_name_2 = "2\\[13, 10, 1, 26, 0__7067_episodes_2019-06-20_08-26-43.245763"
game_map_name_3 = "3\\[14, 16, 1, 18, 0.75, 0.25]_2019-06-20_08-25-50"
results_file_name_3 = "3\\[14, 16, 1, 18, 0__7055_episodes_2019-06-20_08-25-52.462496"
game_map_name_4 = "4\\[16, 16, 3, 20, 0.75, 0.25]_2019-06-20_08-23-40"
results_file_name_4 = "4\\[16, 16, 3, 20, 0__7019_episodes_2019-06-20_08-23-41.690025"
game_map_name_5 = "5\\[16, 16, 3, 22, 0.75, 0.25]_2019-06-20_08-04-55"
results_file_name_5 = "5\\[16, 16, 3, 22, 0__6740_episodes_2019-06-20_08-04-58.276684"
game_map_name_6 = "6\\[10, 16, 4, 16, 0.75, 0.25]_2019-06-20_07-54-26"
results_file_name_6 = "6\\[10, 16, 4, 16, 0__6616_episodes_2019-06-20_07-54-28.899882"
game_map_name_7 = "7\\[14, 8, 2, 22, 0.75, 0.25]_2019-06-20_07-52-31"
results_file_name_7 = "7\\[14, 8, 2, 22, 0__6594_episodes_2019-06-20_07-52-33.302850"
game_map_name_8 = "8\\[17, 17, 2, 17, 0.75, 0.25]_2019-06-20_08-01-57"
results_file_name_8 = "8\\[17, 17, 2, 17, 0__6695_episodes_2019-06-20_08-02-00.488876"
game_map_name_9 = "9\\[8, 12, 2, 17, 0.75, 0.25]_2019-06-20_07-59-50"
results_file_name_9 = "9\\[8, 12, 2, 17, 0__6674_episodes_2019-06-20_07-59-52.326428"
game_map_name_10 = "10\\[14, 11, 2, 22, 0.75, 0.25]_2019-06-20_07-28-02"
results_file_name_10 = "10\\[14, 11, 2, 22, 0__6341_episodes_2019-06-20_07-28-06.405573"

if __name__ == "__main__":
    # input_moves = Utils.get_moves_from_record_file("manual_games\\simple_level_3_2019-06-02_11-03-31.txt")
    # input_moves, rotations = Utils.get_input_moves_list_starting_with("learned_games", LEVEL)
    input_moves, rotations = Utils.get_input_moves_and_rotation_from_file("learned_games_with_map_generator",
                                                                      results_file_name_6)
    # print(input_moves)
    # print("Num of input moves: ", len(input_moves))
    # print("Rotations: ", rotations)
    # # input_moves = Utils.get_example_moves()
    # # input_moves = None
    #
    # RecordSaver.record_path = Utils.get_record_path(sys.argv)
    game_map = Utils.read_map_from_file_path("learned_games_with_map_generator", game_map_name_6)
    # Utils.set_width_and_height(game_map)
    #
    arcade_view = ArcadeView(game_map)
    #
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
