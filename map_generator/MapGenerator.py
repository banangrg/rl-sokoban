import asyncio
import copy
import itertools
from operator import add
from random import randint, shuffle

import arcade

from map_generator import MapGeneratorConfig, Utils
from map_generator.BlockType import BlockType
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum
from map_generator.MapSaver import save_game_map_and_return_file_name
from map_generator.MovementArrayEnum import MovementArrayEnum

action_type_list = [MapGeneratorPlayerActionEnum.PULL_CHEST, MapGeneratorPlayerActionEnum.CHANGE_SIDE]
movement_direction_list = [MovementArrayEnum.DOWN, MovementArrayEnum.RIGHT, MovementArrayEnum.LEFT,
                           MovementArrayEnum.UP]

game_map = []
chest_positions = []
player_position = []
focus_chest = 0


def set_testing_player_position(x, y):
    global game_map, player_position
    game_map[x][y] = BlockType.PLAYER
    player_position = [x, y]


def set_testing_chest(x, y):
    game_map[x][y] = BlockType.CHEST
    chest_positions.append([x, y])


def set_parameters(map_width, map_height, num_of_chests, num_of_moves):
    MapGeneratorConfig.MAP_WIDTH = map_width
    MapGeneratorConfig.MAP_HEIGHT = map_height
    MapGeneratorConfig.NUM_OF_CHESTS = num_of_chests
    MapGeneratorConfig.NUM_OF_MOVES = num_of_moves


def generate_map(map_width=MapGeneratorConfig.MAP_WIDTH, map_height=MapGeneratorConfig.MAP_HEIGHT,
                 num_of_chests=MapGeneratorConfig.NUM_OF_CHESTS, num_of_moves=MapGeneratorConfig.NUM_OF_MOVES):
    set_parameters(map_width, map_height, num_of_chests, num_of_moves)
    init_map(MapGeneratorConfig.MAP_WIDTH, MapGeneratorConfig.MAP_HEIGHT, MapGeneratorConfig.NUM_OF_CHESTS)
    # set_testing_player_position(2, 9)
    # set_testing_chest(1, 9)
    # move_player_to_point([1, 10])
    drill_map(MapGeneratorConfig.NUM_OF_MOVES)

    # show_view_and_print_game_map()
    return game_map, save_game_map_and_return_file_name(game_map)


def draw_action_type():
    action_num = Utils.weighted_choice_king(
        [x.value for x in action_type_list])
    action_type = action_type_list[action_num]
    # # print(action_type)
    return action_type


def move_field_leaving_empty(field, movement_array):
    field_type = game_map[field[0]][field[1]]
    new_position = get_field_after_move(field, movement_array)
    if not is_point_inside_map(new_position):
        # print("move_field_leaving_empty: New position outside map! ", new_position)
        return field
    elif get_field_type(new_position) == BlockType.CHEST or get_field_type(new_position) == BlockType.CHEST_ON_GOAL:
        # print("Next field is chest!")
        return field
    else:
        field_types_to_set = get_block_types_after_move(field_type, get_field_type(new_position))
        game_map[new_position[0]][new_position[1]] = field_types_to_set[0]
        game_map[field[0]][field[1]] = field_types_to_set[1]
        return new_position


def get_block_types_after_move(current_field_type, next_field_type):
    first_field_type = current_field_type
    second_field_type = BlockType.EMPTY
    if next_field_type == BlockType.GOAL:
        if current_field_type == BlockType.PLAYER:
            first_field_type = BlockType.PLAYER_ON_GOAL
        elif current_field_type == BlockType.CHEST:
            first_field_type = BlockType.CHEST_ON_GOAL
        # else:
        # print("get_block_types_after_move: Incorrect current_field_type - ", current_field_type)

    if current_field_type == BlockType.CHEST_ON_GOAL or current_field_type == BlockType.PLAYER_ON_GOAL:
        second_field_type = BlockType.GOAL

    if current_field_type == BlockType.CHEST_ON_GOAL:
        second_field_type = BlockType.GOAL
        first_field_type = BlockType.CHEST
    elif current_field_type == BlockType.PLAYER_ON_GOAL:
        second_field_type = BlockType.GOAL
        first_field_type = BlockType.PLAYER

    return [first_field_type, second_field_type]


def pull_chest():
    # print("Pull chest")
    global player_position
    movement_array = [a - b for a, b in zip(player_position, chest_positions[focus_chest])]
    field_after_move = get_field_after_move(player_position, movement_array)

    if is_point_inside_map(field_after_move) and get_field_type(field_after_move) != BlockType.CHEST and get_field_type(
            field_after_move) != BlockType.CHEST_ON_GOAL:
        player_position = move_field_leaving_empty(player_position, movement_array)
        chest_positions[focus_chest] = move_field_leaving_empty(chest_positions[focus_chest],
                                                                movement_array)
    # else:
    # print("Can't pull, edge ahead!")


def pick_point_on_side_of_the_chest_to_go_to(chest_num):
    possible_points = []
    for movement_direction in movement_direction_list:
        point = get_field_after_move(chest_positions[chest_num], movement_direction.value)
        if is_point_inside_map(point):
            point_type = get_field_type(point)
            if point_type in [BlockType.WALL, BlockType.EMPTY, BlockType.GOAL]:
                possible_points.append(point)
    # print("Possible points: ", possible_points)
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
            # print("Move permutation unsuccessful")
            is_path_successful = False
            break
        else:
            player_position = new_position

    if not is_path_successful:
        game_map = copy.deepcopy(game_map_backup)
        player_position = copy.deepcopy(player_position_backup)
    # else:
    # print("Sucessful permutation: ", moves_permutation)
    return is_path_successful


def move_player_to_point(point_to_go_to):
    # print("Player position: ", player_position, ";  point_to_go: ", point_to_go_to)
    complete_movement_array = [a - b for a, b in zip(point_to_go_to, player_position)]
    # print("complete_movement_array: ", complete_movement_array)



    x_direction = MovementArrayEnum.DOWN
    y_direction = MovementArrayEnum.RIGHT
    if complete_movement_array[0] < 0:
        x_direction = MovementArrayEnum.UP
    if complete_movement_array[1] < 0:
        y_direction = MovementArrayEnum.LEFT
    # print("x_sign = ", x_direction, "; y_sign = ", y_direction)

    moves_array = []
    for i in range(0, abs(complete_movement_array[0])):
        moves_array.append(x_direction)
    for i in range(0, abs(complete_movement_array[1])):
        moves_array.append(y_direction)
    # print("moves_array = ", moves_array)
    # print("moves_array length= ", len(moves_array))
    if len(moves_array) > 10:
        return None

    # moves_array_permutations = list(itertools.permutations(moves_array))
    # # print("moves_array_permutations = ", moves_array_permutations)

    for moves_permutation in set(list(itertools.permutations(moves_array))):
        # Utils.print_enum_list("Executing move permutation:", moves_permutation)
        is_path_successful = execute_player_path(moves_permutation)
        if is_path_successful:
            break
    return True


def change_side():
    # print('Change side')
    point_to_go_to = pick_point_on_side_of_the_chest_to_go_to(focus_chest)
    move_player_to_point(point_to_go_to)


def go_to_another_chest():
    # print("Go to another chest")
    global focus_chest
    focus_chest += 1
    point_to_go_to = pick_point_on_side_of_the_chest_to_go_to(focus_chest)
    moving_result = move_player_to_point(point_to_go_to)
    if moving_result is None:
        focus_chest -= 1


def run_action_type(action_type):
    switcher = {
        MapGeneratorPlayerActionEnum.PULL_CHEST: pull_chest,
        MapGeneratorPlayerActionEnum.CHANGE_SIDE: change_side,
        MapGeneratorPlayerActionEnum.GO_TO_ANOTHER_CHEST: go_to_another_chest
    }
    func = switcher.get(action_type, lambda: "Invalid action type")
    return func()


def drill_map(num_of_moves):
    actions = []
    for i in range(0, len(chest_positions) - 1):
        actions.append(MapGeneratorPlayerActionEnum.GO_TO_ANOTHER_CHEST)
    for i in range(0, num_of_moves):
        actions.append(draw_action_type())
    shuffle(actions)
    # Utils.print_enum_list("Actions", actions)
    for i in range(0, num_of_moves):
        run_action_type(actions[i])
        # Utils.print_game_map(game_map)


def generate_chests(num_chests, x, y):
    for i in range(0, num_chests):
        while True:
            chest_x = randint(1, x - 2)
            chest_y = randint(1, y - 2)
            if game_map[chest_x][chest_y] is BlockType.WALL:
                game_map[chest_x][chest_y] = BlockType.CHEST_ON_GOAL
                chest_positions.append([chest_x, chest_y])
                break


def generate_player():
    global focus_chest
    global player_position
    # chest_near_player_num = randint(0, len(chest_positions) - 1)
    start_chest_position = chest_positions[focus_chest]

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

    # print("Possible start points:", possible_start_points)
    return possible_start_points


def get_field_after_move(position, movement_array):
    return list(map(add, position, movement_array))


def get_field_type(position):
    return game_map[position[0]][position[1]]


# def show_view_and_print_game_map():
# Utils.print_game_map(game_map)
# ArcadeView(game_map)
# asyncio.run(arcade.run())

# arcade_thread = ArcadeThread(game_map)
# arcade_thread.start()
# print("sochacki")


# class ArcadeThread(threading.Thread):
#     def __init__(self, game_map):
#         super(ArcadeThread, self).__init__()
#         self.game_map = game_map
#
#     def run(self):
#         ArcadeView(self.game_map)
#         arcade.run()


def reset_map_generator_variables():
    global game_map, chest_positions, player_position, focus_chest
    game_map = []
    chest_positions = []
    player_position = []
    focus_chest = 0


def init_map(x, y, num_chests, test_mode=False):
    reset_map_generator_variables()
    generate_all_wall_fields(x, y)

    if not test_mode:
        generate_chests(num_chests, x, y)
        # print("Chest positions: ", chest_positions)
        generate_player()
        # print("Player position: ", player_position)
    # Utils.print_game_map(game_map)


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
