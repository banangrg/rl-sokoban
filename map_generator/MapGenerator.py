import asyncio
import copy
from operator import add
from random import randint
import itertools

import arcade

import Utils
from ArcadeView import ArcadeView
from BlockType import BlockType
from map_generator import MapGeneratorConfig
from map_generator.MovementArrayEnum import MovementArrayEnum
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum

action_type_list = [MapGeneratorPlayerActionEnum.PULL_CHEST, MapGeneratorPlayerActionEnum.CHANGE_SIDE]
movement_direction_list = [MovementArrayEnum.DOWN, MovementArrayEnum.RIGHT, MovementArrayEnum.LEFT,
                           MovementArrayEnum.UP]

game_map = []
chest_positions = []
player_position = []
chest_near_player_num = -1


def set_testing_player_position(x, y):
    global game_map, player_position
    game_map[x][y] = BlockType.PLAYER
    player_position = [x, y]
    pass


def generate_map(x, y, num_chests=10):
    init_map(x, y, num_chests)
    # set_testing_player_position(5, 6)
    # game_map[2][5] = BlockType.CHEST
    move_player_to_point([2, 3])
    # make_path(MapGeneratorConfig.NUM_OF_MOVES)

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
    if not is_point_inside_map(new_position):
        print("move_field_leaving_empty: New position outside map! ", new_position)
        return field
    elif get_field_type(new_position) == BlockType.CHEST:
        print("Next field is chest!")
        return field
    else:
        game_map[new_position[0]][new_position[1]] = field_type
        game_map[field[0]][field[1]] = BlockType.EMPTY
        return new_position


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


def pick_point_on_side_of_the_chest_to_go_to():
    possible_points = []
    for movement_direction in movement_direction_list:
        point = get_field_after_move(chest_positions[chest_near_player_num], movement_direction.value)
        if is_point_inside_map(point):
            point_type = get_field_type(point)
            if point_type in [BlockType.WALL, BlockType.EMPTY, BlockType.GOAL]:
                possible_points.append(point)
    print("Possible points: ", possible_points)
    num = randint(0, len(possible_points) - 1)
    return possible_points[num]


def execute_player_path(moves_permutation):
    global game_map, player_position
    is_path_successful = True
    game_map_backup = copy.deepcopy(game_map)
    player_position_backup = copy.deepcopy(player_position)

    for move in moves_permutation:
        new_position = move_field_leaving_empty(player_position, move.value)
        if new_position == player_position:
            print("Move permutation unsuccessful")
            is_path_successful = False
            break
        else:
            player_position = new_position

    if not is_path_successful:
        game_map = copy.deepcopy(game_map_backup)
        player_position = copy.deepcopy(player_position_backup)
    else:
        print("Sucessful permutation: ", moves_permutation)
    return is_path_successful


def move_player_to_point(point_to_go_to):
    print("Player position: ", player_position, ";  point_to_go: ", point_to_go_to)
    complete_movement_array = [a - b for a, b in zip(point_to_go_to, player_position)]
    print("complete_movement_array: ", complete_movement_array)

    x_direction = MovementArrayEnum.RIGHT
    y_direction = MovementArrayEnum.UP
    if complete_movement_array[0] < 0:
        x_direction = MovementArrayEnum.LEFT
    if complete_movement_array[1] < 0:
        y_direction = MovementArrayEnum.DOWN
    print("x_sign = ", x_direction, "; y_sign = ", y_direction)

    moves_array = []
    for i in range(0, abs(complete_movement_array[0])):
        moves_array.append(x_direction)
    for i in range(0, abs(complete_movement_array[1])):
        moves_array.append(y_direction)
    print("moves_array = ", moves_array)

    moves_array_permutations = list(itertools.permutations(moves_array))
    print("moves_array_permutations = ", moves_array_permutations)

    # test_per = [MovementArrayEnum.LEFT, MovementArrayEnum.LEFT, MovementArrayEnum.DOWN, MovementArrayEnum.DOWN,
    #             MovementArrayEnum.LEFT, MovementArrayEnum.DOWN]
    # execute_player_path(test_per)

    for moves_permutation in moves_array_permutations:
        print("Executing move permutation:")
        for move_enum in moves_permutation:
            print(move_enum.name, end=",")
        print()
        is_path_successful = execute_player_path(moves_permutation)
        if is_path_successful:
            break


def change_side():
    print('Change side')
    point_to_go_to = pick_point_on_side_of_the_chest_to_go_to()
    move_player_to_point(point_to_go_to)


def run_action_type(action_type):
    switcher = {
        MapGeneratorPlayerActionEnum.PULL_CHEST: pull_chest,
        MapGeneratorPlayerActionEnum.CHANGE_SIDE: change_side

    }
    func = switcher.get(action_type, lambda: "Invalid action type")
    return func()


def make_action():
    action_type = draw_action_type()
    run_action_type(action_type)

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
    return game_map[position[0]][position[1]]


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

def find_player():
    for i in range(len(game_map)):
        for j in range(len(game_map[i])):
            if game_map[i][j] == BlockType.PLAYER or game_map[i][j] == BlockType.PLAYER_ON_GOAL:
                return [i, j]
