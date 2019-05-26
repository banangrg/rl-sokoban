import asyncio
from operator import add
from random import randint

import arcade

import Utils
from ArcadeView import ArcadeView
from BlockType import BlockType
from map_generator import MapGeneratorConfig
from map_generator.MovementArrayEnum import MovementArrayEnum
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum

action_type_list = [MapGeneratorPlayerActionEnum.PULL_CHEST, MapGeneratorPlayerActionEnum.CHANGE_SIDE]

game_map = []
chest_positions = []
player_position = []
chest_near_player_num = -1


def generate_map(x, y, num_chests=1):
    init_map(x, y, num_chests)
    make_path(MapGeneratorConfig.NUM_OF_MOVES)

    show_view_and_print_game_map()


def draw_action_type():
    action_num = Utils.weighted_choice_king(
        [x.value for x in action_type_list])
    action_type = action_type_list[action_num]
    # print(action_type)
    return action_type


def move_field_leaving_empty(field, movement_array):
    field_type = game_map[field[0]][field[1]]
    new_position = get_field_after_move(field, movement_array)
    if is_point_inside_map(new_position):
        game_map[new_position[0]][new_position[1]] = field_type
        game_map[field[0]][field[1]] = BlockType.EMPTY
        return new_position
    else:
        print("move_field_leaving_empty: New position outside map!")
        return field


def pull_chest():
    print("Pull chest")
    global player_position
    movement_array = [a - b for a, b in zip(player_position, chest_positions[chest_near_player_num])]

    if is_point_inside_map(get_field_after_move(player_position, movement_array)):
        player_position = move_field_leaving_empty(player_position, movement_array)
        chest_positions[chest_near_player_num] = move_field_leaving_empty(chest_positions[chest_near_player_num],
                                                                          movement_array)
    else:
        print("Can't pull, edge ahead!")


def change_side():
    print('Change side')


def action_type_to_function(action_type):
    switcher = {
        MapGeneratorPlayerActionEnum.PULL_CHEST: pull_chest,
        MapGeneratorPlayerActionEnum.CHANGE_SIDE: change_side

    }
    func = switcher.get(action_type, lambda: "Invalid action type")
    return func()


def make_action():
    action_type = draw_action_type()
    action_type_to_function(action_type)

    pass


def make_path(num_of_moves):
    for i in range(1, num_of_moves):
        make_action()
        Utils.print_game_map(game_map)
    pass


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
    global chest_near_player_num
    global player_position
    chest_near_player_num = randint(0, len(chest_positions) - 1)
    start_chest_position = chest_positions[chest_near_player_num]

    possible_start_points = get_possible_start_points(start_chest_position)
    start_point_num = randint(0, len(possible_start_points) - 1)
    start_point = possible_start_points[start_point_num]

    game_map[start_point[0]][start_point[1]] = BlockType.PLAYER
    player_position = [start_point[0], start_point[1]]


def is_point_inside_map(point):
    if point[0] <= 0 or point[0] >= len(game_map) - 1:
        return False
    elif point[1] <= 0 or point[1] >= len(game_map[0]) - 1:
        return False
    else:
        return True


def get_possible_start_points(chest_position):
    fields_around_chest = []
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.LEFT.value))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.RIGHT.value))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.UP.value))
    fields_around_chest.append(get_field_after_move(chest_position, MovementArrayEnum.DOWN.value))

    possible_start_points = []
    for start_point in fields_around_chest:
        if is_point_inside_map(start_point):
            possible_start_points.append(start_point)

    print("Possible start points:", possible_start_points)
    return possible_start_points


def get_field_after_move(position, movement_array):
    return list(map(add, position, movement_array))


def get_field_type(position):
    return game_map[position[0], position[1]]


def show_view_and_print_game_map():
    Utils.print_game_map(game_map)
    ArcadeView(game_map)
    asyncio.run(arcade.run())


def init_map(x, y, num_chests):
    generate_all_wall_fields(x, y)

    generate_chests(num_chests, x, y)
    print(chest_positions)
    generate_player()


def generate_all_wall_fields(x, y):
    for i in range(x):
        line = []
        for j in range(y):
            line.append(BlockType.WALL)
        game_map.append(line)
