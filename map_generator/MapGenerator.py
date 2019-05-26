import asyncio
from operator import add
from random import randint

import arcade

import Utils
from ArcadeView import ArcadeView
from BlockType import BlockType
from map_generator.MovementArrayEnum import MovementArrayEnum

game_map = []
chest_positions = []
player_position = []


def generate_map(x, y, num_chests=3):
    init_map(x, y)

    generate_chests(num_chests, x, y)
    print(chest_positions)
    generate_player()

    show_view_and_print_game_map()


def generate_chests(num_chests, x, y):
    for i in range(0, num_chests):
        while True:
            chest_x = randint(1, x - 2)
            chest_y = randint(1, y - 2)
            if game_map[chest_x][chest_y] is BlockType.WALL:
                game_map[chest_x][chest_y] = BlockType.CHEST
                chest_positions.append([chest_x, chest_y])
                break


def generate_player():
    near_chest_num = randint(0, len(chest_positions) - 1)
    start_chest_position = chest_positions[near_chest_num]

    possible_start_points = get_possible_start_points(start_chest_position)
    start_point_num = randint(0, len(possible_start_points) - 1)
    start_point = possible_start_points[start_point_num]

    game_map[start_point[0]][start_point[1]] = BlockType.PLAYER


def is_point_inside_map(point):
    if point[0] <= 0 or point[0] >= len(game_map) - 1:
        return False
    elif point[1] <= 0 or point[1] >= len(game_map[0]) - 1:
        return False
    else:
        return True


def get_possible_start_points(chest_position):
    fields_around_chest = []
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.LEFT))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.RIGHT))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.UP))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.DOWN))

    possible_start_points = []
    for start_point in fields_around_chest:
        if is_point_inside_map(start_point):
            possible_start_points.append(start_point)

    print("Possible start points:", possible_start_points)
    return possible_start_points


def get_field_after_move(position, movement_array_enum):
    return list(map(add, position, movement_array_enum.value))


def show_view_and_print_game_map():
    Utils.print_game_map(game_map)
    ArcadeView(game_map)
    asyncio.run(arcade.run())


def init_map(x, y):
    for i in range(x):
        line = []
        for j in range(y):
            line.append(BlockType.WALL)
        game_map.append(line)
