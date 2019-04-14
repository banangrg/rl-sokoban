import arcade
import sys

import SobParams as cs
from BlockType import BlockType


def draw_field_at(x, y, block_type):
    arcade.draw_xywh_rectangle_filled(x * cs.FIELD_WIDTH, y * cs.FIELD_HEIGHT, cs.FIELD_WIDTH, cs.FIELD_HEIGHT,
                                      block_type.get_color())


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


def draw_map(map):
    print(type(map))
    for i in range(len(map)):
        for j in range(len(map[i])):
            if BlockType(map[i][j]) == BlockType.PLAYER:
                player_position = [i, j]
            draw_field_at(i, j, BlockType(map[i][j]))
    return player_position


def get_level_path(argv):
    level_path = cs.PATH_TO_LEVELS
    if len(argv) > 1:
        level_path += argv[1]
        if argv[1] == '-h' or argv[1] == '--help':
            print(
                "First argument is name of file with level, path to levels directory is already present. Example cmd: python SokobanGame.py simplest_possible_level.txt")
            sys.exit(0)
    else:
        level_path += cs.DEFAULT_LEVEL
    return level_path


def read_map_from_file_path(file_path):
    lines = []
    with open(file_path) as map_file:
        for line in map_file:
            line = line.replace('\n', '')
            lines.append(list(line))
    return lines


def set_width_and_height(game_map):
    cs.WINDOW_WIDTH = len(game_map) * cs.FIELD_WIDTH
    cs.WINDOW_HEIGHT = len(game_map[0]) * cs.FIELD_HEIGHT
