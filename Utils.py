import sys

import SobParams as SobParams
from BlockType import BlockType


# from ArcadeView import draw_field_at


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


def read_map_from_file_path(file_path):
    lines = []
    with open(file_path) as map_file:
        for line in map_file:
            line = line.replace('\n', '')
            lines.append(list(line))
    return lines


def set_width_and_height(game_map):
    SobParams.WINDOW_WIDTH = len(game_map) * SobParams.FIELD_WIDTH
    SobParams.WINDOW_HEIGHT = len(game_map[0]) * SobParams.FIELD_HEIGHT


def get_example_moves():
    return "L;U;R;D;" * 10


def get_moves_from_record_file(file_name):
    file = open("manual_games\\" + file_name, "r")
    content = file.read()
    lines = content.split("\n")
    return lines[1]


def print_game_map(game_map):
    for row in game_map:
        for column in row:
            print(column.value, end="")
        print("")
