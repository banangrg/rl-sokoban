import sys
import random
import bisect
import os
from numpy import array
import numpy

from map_generator.BlockType import BlockType


def generate_example_map():
    example_map = []

    top_row = []
    for i in range(0, 10):
        top_row.append('#')
    example_map.append(top_row)

    middle_row = ['#', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '#']
    for i in range(0, 8):
        example_map.append(middle_row.copy())

    example_map.append(top_row.copy())
    example_map[5][5] = BlockType.PLAYER

    add_some_walls(example_map)
    example_map[2][3] = BlockType.CHEST
    example_map[2][2] = BlockType.GOAL

    return example_map


def add_some_walls(example_map):
    example_map[3][2] = BlockType.WALL
    example_map[5][7] = BlockType.WALL
    example_map[8][4] = BlockType.WALL


def get_level_name(argv):
    level_path = ""
    if len(argv) > 1:
        level_path += argv[1]
        if argv[1] == '-h' or argv[1] == '--help':
            print(
                "First argument is name of file with level, path to levels directory is already present. Example cmd: python SokobanGame.py simplest_possible_level.txt")
            sys.exit(0)
    else:
        level_path += SobParams.DEFAULT_LEVEL
    return level_path


def get_level_path(argv):
    level_path = SobParams.PATH_TO_LEVELS
    level_name = get_level_name(argv)
    return level_path + level_name


def get_record_path(argv):
    record_path = SobParams.PATH_TO_MANUAL_GAMES
    level_name = get_level_name(argv)
    return record_path + level_name


def read_map_from_file_path(folder_name, file_name):
    # SobParams.DEFAULT_LEVEL = file_path.split("\\")[1]
    file_path = folder_name + "\\" + file_name + ".txt"
    lines = []
    with open(file_path) as map_file:
        for line in map_file:
            line = line.replace('\n', '')
            lines.append(list(line))
    return lines


def set_width_and_height(game_map):
    # SobParams.WINDOW_WIDTH = len(game_map) * SobParams.FIELD_WIDTH
    # SobParams.WINDOW_HEIGHT = len(game_map[0]) * SobParams.FIELD_HEIGHT
    width = len(game_map) * SobParams.FIELD_WIDTH
    height = len(game_map[0]) * SobParams.FIELD_HEIGHT
    size_to_set = width
    if height > width:
        size_to_set = height
    SobParams.WINDOW_WIDTH = size_to_set
    SobParams.WINDOW_HEIGHT = size_to_set


def get_example_moves():
    return "L;U;R;D;" * 10


def read_line_of_file(file_name, line_num):
    file = open(file_name, "r")
    content = file.read()
    lines = content.split("\n")
    return lines[line_num]


def get_input_moves_list_starting_with(folder_name, level_name):
    inputs_list = []
    rotations = []
    files = [i for i in os.listdir(folder_name) if
             os.path.isfile(os.path.join(folder_name, i)) and level_name in i]
    precise_files = []
    [precise_files.append(file) for file in files if file.split("__")[0] == level_name]
    files = precise_files
    files.sort(key=lambda x: x.split("episodes_")[1])
    # [print(f) for f in files]

    [inputs_list.append(read_line_of_file(folder_name + "\\" + file_name, 1)) for file_name in files]
    [rotations.append(int(read_line_of_file(folder_name + "\\" + file_name, 4))) for file_name in files]
    return inputs_list, rotations


def print_game_map(game_map):
    for row in game_map:
        for column in row:
            print(column.value, end="")
        print("")


def get_string_game_map(game_map):
    string_game_map = ""
    for row in game_map:
        for column in row:
            string_game_map += column.value
        string_game_map += "\n"
    return string_game_map


def weighted_choice_b(weights):
    totals = []
    running_total = 0

    for w in weights:
        running_total += w
        totals.append(running_total)

    rnd = random.random() * running_total
    return bisect.bisect_right(totals, rnd)


def weighted_choice_king(weights):
    total = 0
    winner = 0
    for i, w in enumerate(weights):
        total += w
        if random.random() * total < w:
            winner = i
    return winner


def print_enum_list(name, list_to_print):
    print(name, end=": ")
    [print(x.name, end=", ") for x in list_to_print]
    print()


def rotate_map(game_map, rotation):
    game_map = array(game_map)
    if rotation >= 0:
        game_map = numpy.rot90(game_map, rotation)
    elif rotation == -1:
        game_map = numpy.fliplr(game_map)
    elif rotation == -2:
        game_map = numpy.flipud(game_map)
    else:
        raise Exception("Wrong rotation: ", rotation)
    return game_map.tolist()
