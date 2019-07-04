import os
import time
import argparse
import datetime
import threading
import numpy as np
from pynput import keyboard
from random import randint
from map_generator.MapGenerator import generate_map


# # - wall
# SPACE - free space
# $ - box
# . - target for boxes
# * - box on target
# @ - player
# + - player on target


class AbstractRewardSystem:
    @staticmethod
    def get_reward_for_move():
        raise NotImplementedError("Please Implement this method")

    @staticmethod
    def get_reward_for_box_on_target():
        raise NotImplementedError("Please Implement this method")

    @staticmethod
    def get_reward_for_box_off_target():
        raise NotImplementedError("Please Implement this method")

    @staticmethod
    def get_reward_for_invalid_move():
        raise NotImplementedError("Please Implement this method")

    @staticmethod
    def get_reward_for_victory():
        raise NotImplementedError("Please Implement this method")

    @staticmethod
    def get_reward_for_loss():
        raise NotImplementedError("Please Implement this method")


class RewardSystem(AbstractRewardSystem):
    @staticmethod
    def get_reward_for_move():
        """ for move without any effect """
        return -0.05

    @staticmethod
    def get_reward_for_box_on_target():
        return 8.0

    @staticmethod
    def get_reward_for_box_off_target():
        return -8.0

    @staticmethod
    def get_reward_for_invalid_move():
        return -3.0

    @staticmethod
    def get_reward_for_victory():
        return 30.0

    @staticmethod
    def get_reward_for_loss():
        return -30.0


class SokobanGame:
    # class variables
    WALL = '#'
    FREE_SPACE = ' '
    BOX = '$'
    TARGET = '.'
    BOX_ON_TARGET = '*'
    PLAYER = '@'
    PLAYER_ON_TARGET = '+'

    MOVE_LEFT = 'L'
    MOVE_RIGHT = 'R'
    MOVE_UP = 'U'
    MOVE_DOWN = 'D'

    DEFAULT_TIMEOUT = 200   # max number of moves before game ends with loss

    MAP_ROTATION_NONE = 0
    MAP_ROTATION_90 = 1
    MAP_ROTATION_180 = 2
    MAP_ROTATION_270 = 3
    MAP_ROTATION_FLIP_Y = -1    # flip along y axis - flip left-right
    MAP_ROTATION_FLIP_X = -2    # flip along x axis - flip up-down
    ROTATIONS_STANDARD = [MAP_ROTATION_NONE, MAP_ROTATION_90, MAP_ROTATION_180, MAP_ROTATION_270]
    ROTATIONS_FLIP = [MAP_ROTATION_FLIP_Y, MAP_ROTATION_FLIP_X]
    ROTATIONS_ALL = ROTATIONS_STANDARD + ROTATIONS_FLIP

    PATH_TO_LEVELS = 'levels/'
    PATH_TO_MANUAL_GAMES = 'manual_games/'

    GENERATED_MAP_SIZE_OFFSET = 0
    GENERATED_MAP_MOVE_OFFSET = 0
    GENERATED_MAP_NUM_CHESTS_OFFSET = 0

    GENERATED_MAP_MIN_DIMENSION = 7 + GENERATED_MAP_SIZE_OFFSET
    GENERATED_MAP_MAX_DIMENSION = 16 + GENERATED_MAP_SIZE_OFFSET
    GENERATED_MAP_MIN_NUM_OF_CHESTS = 1 + GENERATED_MAP_NUM_CHESTS_OFFSET
    GENERATED_MAP_MAX_NUM_OF_CHESTS = 3 + GENERATED_MAP_NUM_CHESTS_OFFSET
    GENERATED_MAP_MIN_NUM_OF_MOVES = 15 + GENERATED_MAP_MOVE_OFFSET
    GENERATED_MAP_MAX_NUM_OF_MOVES = 25 + GENERATED_MAP_MOVE_OFFSET

    def __init__(self, path_to_level: str, reward_impl: AbstractRewardSystem, loss_timeout: int = DEFAULT_TIMEOUT,
                 manual_play: bool = True, map_rotation: int = MAP_ROTATION_NONE, use_generated_maps: bool = False):
        """ Initializes single game. Requires path to file with level and a reward system (ex. basic RewardSystem()).
            Does basic validation of loaded level. \n
            If use_generated_maps is set then path_to_level will not matter - map will be generated"""
        # load level
        self.current_level = None
        if use_generated_maps:
            map_width = randint(self.GENERATED_MAP_MIN_DIMENSION, self.GENERATED_MAP_MAX_DIMENSION + 1)
            map_height = randint(self.GENERATED_MAP_MIN_DIMENSION, self.GENERATED_MAP_MAX_DIMENSION + 1)
            num_of_chests = randint(self.GENERATED_MAP_MIN_NUM_OF_CHESTS, self.GENERATED_MAP_MAX_NUM_OF_CHESTS + 1)
            num_of_moves = randint(self.GENERATED_MAP_MIN_NUM_OF_MOVES, self.GENERATED_MAP_MAX_NUM_OF_MOVES + 1)
            while self.current_level is None:
                temp_map, temp_level_name = generate_map(map_width=map_width, map_height=map_height,
                                                         num_of_chests=num_of_chests, num_of_moves=num_of_moves)
                temp_map = self.convert_generated_map_to_numpy_map(temp_map)
                self.current_level = temp_map
            self.path_to_current_level = 'generated_maps/' + temp_level_name
        else:
            self.load_level(path_to_level)
            self.path_to_current_level = path_to_level
            # basic level validation
            validation_ok, reason = self.check_loaded_level_basic_validation()
            if not validation_ok:
                raise Exception(reason)
        if not isinstance(reward_impl, AbstractRewardSystem):
            raise Exception("Invalid reward system")
        # assign instance variables
        self.reward_system = reward_impl
        self.game_timeout = loss_timeout
        self.is_manual = manual_play
        self.move_counter = 0
        self.total_reward = 0.0
        self.moves_made = []
        self.rewards_received = []
        if map_rotation not in self.ROTATIONS_ALL:
            raise Exception("Invalid map rotation option!")
        self.map_rotation = map_rotation
        # rotate map according to setting
        if map_rotation >= 0:   # standard rotation
            self.current_level = np.rot90(self.current_level, k=map_rotation)
        elif map_rotation == self.MAP_ROTATION_FLIP_Y:
            self.current_level = np.fliplr(self.current_level)
        elif map_rotation == self.MAP_ROTATION_FLIP_X:
            self.current_level = np.flipud(self.current_level)

    @staticmethod
    def get_level(filepath: str):
        """ Gets level with specified path as numpy array of characters, does NOT check map validity. \n
            Fills empty spaces outside map with WALL to correctly make numpy matrix
            Throws ValueError if it does not find a WALL in line
        """
        with open(filepath, "r") as f:
            lines = f.readlines()
        lines = [line.rstrip('\r\n') for line in lines]
        characters = []
        line_num = 0
        try:
            longest_line_len = len(max(lines, key=len)) + 1  # +1 is there to account for the empty line we add later
            for line in lines:
                # fill empty spaces outside map with WALL
                index_of_first_wall_in_line = line.index(SokobanGame.WALL)
                index_of_last_wall_in_line = line.rindex(SokobanGame.WALL)

                line = line + SokobanGame.FREE_SPACE    # add one empty space at the end of each line to make it work
                line = SokobanGame.WALL * index_of_first_wall_in_line + \
                       line[index_of_first_wall_in_line : -(len(line) - index_of_last_wall_in_line)] + \
                       SokobanGame.WALL * ((longest_line_len - index_of_last_wall_in_line) - 1)

                # make string a list and add it to list of lists - later converted to numpy array
                chars_line = []
                chars_line.extend(line)
                characters.append(chars_line)

                line_num += 1
            return np.array(characters)
        except ValueError:
            print("ERROR - did not find any WALL (" + SokobanGame.WALL + ") in line " + str(line_num))
            raise

    @staticmethod
    def convert_generated_map_to_numpy_map(list_map):
        """ Translate map from map_generators generate_map function returning list of lists of Enum objects to 2D numpy
            array used by this class
        """
        if list_map is None:
            return None
        for row in range(len(list_map)):
            map_row = list_map[row]
            for col in range(len(map_row)):
                list_map[row][col] = list_map[row][col].value   # get value from enum object
        return np.array(list_map)

    @staticmethod
    def get_rules():
        """ gets list of strings with rules """
        rules = ["List of Sokoban rules: (according to Wikipedia: https://en.wikipedia.org/wiki/Sokoban)",
                 "  1. Player may move horizontally or vertically onto empty squares",
                 "  2. The player can also move into a box, which pushes it into the square beyond",
                 "  3. Boxes may NOT be pushed into other boxes or walls, and they cannot be pulled",
                 "  4. The number of boxes is equal to the number of storage locations",
                 "  5. The game is won when all boxes are at storage locations",
                 "Symbols used:",
                 "  WALL - " + SokobanGame.WALL,
                 "  FREE_SPACE - " + SokobanGame.FREE_SPACE,
                 "  BOX - " + SokobanGame.BOX,
                 "  BOX_ON_TARGET - " + SokobanGame.BOX_ON_TARGET,
                 "  TARGET - " + SokobanGame.TARGET,
                 "  PLAYER - " + SokobanGame.PLAYER,
                 "  PLAYER_ON_TARGET - " + SokobanGame.PLAYER_ON_TARGET,
                 "Controls:",
                 "  up - " + SokobanGame.MOVE_UP,
                 "  down - " + SokobanGame.MOVE_DOWN,
                 "  left - " + SokobanGame.MOVE_LEFT,
                 "  right - " + SokobanGame.MOVE_RIGHT]
        return rules

    @staticmethod
    def print_rules():
        """ prints rules to console """
        for line in SokobanGame.get_rules():
            print(line)

    @staticmethod
    def change_controls(up: str = 'W', down: str = 'S', left: str = 'A', right: str = 'D'):
        SokobanGame.MOVE_UP = up
        SokobanGame.MOVE_DOWN = down
        SokobanGame.MOVE_LEFT = left
        SokobanGame.MOVE_RIGHT = right

    def load_level(self, filepath: str):
        """ loads level with specified path, does NOT check map validity """
        self.current_level = SokobanGame.get_level(filepath)

    def check_loaded_level_basic_validation(self):
        """
        Checks basic validation rules: number of boxes and targets equal, number of players = 1
        """
        boxes_not_on_target_count = (self.current_level == self.BOX).sum()
        target_count = (self.current_level == self.TARGET).sum()
        player_on_target_count = (self.current_level == self.PLAYER_ON_TARGET).sum()
        player_count = (self.current_level == self.PLAYER).sum()
        target_count += player_on_target_count
        player_count += player_on_target_count
        if boxes_not_on_target_count != target_count:
            reason = "VALIDATION FAILED: Number of targets does NOT match number of boxes, boxes: " + str(boxes_not_on_target_count) + \
                ", targets: " + str(target_count) + " map = " + self.path_to_current_level
            print(reason)
            return False, reason
        if player_count != 1:
            reason = "VALIDATION FAILED: Number of players != 1, actual: " + str(player_count) + " map = " + self.path_to_current_level
            print(reason)
            return False, reason
        return True, "OK"

    def get_player_position(self):
        """ gets current position of player in level - first x than y """
        if self.PLAYER_ON_TARGET in self.current_level:
            position = np.where(self.current_level == self.PLAYER_ON_TARGET)
        else:
            position = np.where(self.current_level == self.PLAYER)
        return position[0], position[1]

    def print_current_level(self):
        for row in self.current_level:
            for col in row:
                print(col, end='')
            print("")

    # ------------------ move validators -------------------------------------------------------------------------------------------------------------------------------------
    def position_check(self, check_row_one: int, check_col_one: int, check_row_two: int, check_col_two: int):
        """ Internal move validator used by is_move_up_valid(), is_move_down_valid(), etc.
            Checks if move is possible. Needs index of position one block away and position two blocks away. """
        # dont check index out of bounds for position one because there is always at least one wall on borders
        el_distance_one = self.current_level[check_row_one, check_col_one]
        if el_distance_one == self.WALL:     # if wall is on position one move is invalid
            return False
        if check_row_two >= 0 and check_col_two >= 0:  # check for index out of bounds
            el_distance_two = self.current_level[check_row_two, check_col_two]
            if el_distance_one == self.BOX or el_distance_one == self.BOX_ON_TARGET:  # if box is on position one
                if el_distance_two == self.WALL or el_distance_two == self.BOX or el_distance_two == self.BOX_ON_TARGET:    # and if wall OR box OR box_on_target is on position two move is invalid
                    return False
        return True

    def is_move_up_valid(self):
        player_row, player_col = self.get_player_position()
        return self.position_check(player_row - 1, player_col, player_row - 2, player_col)

    def is_move_down_valid(self):
        player_row, player_col = self.get_player_position()
        return self.position_check(player_row + 1, player_col, player_row + 2, player_col)

    def is_move_left_valid(self):
        player_row, player_col = self.get_player_position()
        return self.position_check(player_row, player_col - 1, player_row, player_col - 2)

    def is_move_right_valid(self):
        player_row, player_col = self.get_player_position()
        return self.position_check(player_row, player_col + 1, player_row, player_col + 2)

    # ------------------ move handlers -------------------------------------------------------------------------------------------------------------------------------------
    def put_specified_element_on_target(self, row: int, col: int, element_to_put: str):
        """ changes target row,col to specified element, does NOT provide checking if move is valid """
        self.current_level[row, col] = element_to_put

    def move_internal(self, player_pos_row: int, player_pos_col: int, pos_one_row: int, pos_one_col: int,
                      pos_two_row: int, pos_two_col: int):
        """
        internal method for making move \n
        Does NOT provide checking if move is valid, behavior is undefined if move is invalid
        """
        # first get elements in original position
        el_distance_zero = self.current_level[player_pos_row, player_pos_col]
        el_distance_one = self.current_level[pos_one_row, pos_one_col]
        el_distance_two = self.current_level[pos_two_row, pos_two_col]
        tgt_distance_zero, tgt_distance_one, tgt_distance_two = 'X', 'X', 'X'    # initialize elements that will replace original ones - if such symbol is present somewhere it means that this method has a bug
        is_pos_two_replacement_needed = False       # when box is not pushed replacement of element in position two is not needed

        # first element zero - player
        if el_distance_zero == self.PLAYER_ON_TARGET:   # if player was on target replace with target
            tgt_distance_zero = self.TARGET
        elif el_distance_zero == self.PLAYER:   # if player was not on target replace with free space
            tgt_distance_zero = self.FREE_SPACE

        # than element one
        if el_distance_one == self.FREE_SPACE or el_distance_one == self.BOX:  # if next position was free space or box replace with player
            tgt_distance_one = self.PLAYER
        elif el_distance_one == self.TARGET or el_distance_one == self.BOX_ON_TARGET:    # if next position was target or box_on_target replace with player_on_target
            tgt_distance_one = self.PLAYER_ON_TARGET

        # than element two
        if (el_distance_one == self.BOX or el_distance_one == self.BOX_ON_TARGET) and el_distance_two == self.FREE_SPACE:   # if there was box in position one AND position two is free replace with box
            tgt_distance_two = self.BOX
            is_pos_two_replacement_needed = True    # indicate that replacement of position two is needed because position one was box
        elif (el_distance_one == self.BOX or el_distance_one == self.BOX_ON_TARGET) and el_distance_two == self.TARGET:   # if there was box in position one AND position two is target replace with box on target
            tgt_distance_two = self.BOX_ON_TARGET
            is_pos_two_replacement_needed = True    # indicate that replacement of position two is needed because position one was box

        # lastly make changes on game map
        self.put_specified_element_on_target(player_pos_row, player_pos_col, element_to_put=tgt_distance_zero)
        self.put_specified_element_on_target(pos_one_row, pos_one_col, element_to_put=tgt_distance_one)
        if is_pos_two_replacement_needed:
            self.put_specified_element_on_target(pos_two_row, pos_two_col, element_to_put=tgt_distance_two)

    def is_new_box_on_target(self, old_game_state):
        boxes_on_target_old = (old_game_state == self.BOX_ON_TARGET).sum()
        boxes_on_target_new = (self.current_level == self.BOX_ON_TARGET).sum()
        if boxes_on_target_new > boxes_on_target_old:
            return True
        else:
            return False

    def is_new_box_off_target(self, old_game_state):
        boxes_on_target_old = (old_game_state == self.BOX_ON_TARGET).sum()
        boxes_on_target_new = (self.current_level == self.BOX_ON_TARGET).sum()
        if boxes_on_target_new < boxes_on_target_old:
            return True
        else:
            return False

    def get_reward_for_move(self, old_game_state):
        if self.is_new_box_on_target(old_game_state):
            reward = self.reward_system.get_reward_for_box_on_target()
        elif self.is_new_box_off_target(old_game_state):
            reward = self.reward_system.get_reward_for_box_off_target()
        else:
            reward = self.reward_system.get_reward_for_move()

        self.add_reward_to_game_memory(reward)
        return reward

    def handle_invalid_move(self, do_print_message: bool = False):
        if do_print_message:
            print("     >>> Invalid move!")
        reward_for_invalid_move = self.reward_system.get_reward_for_invalid_move()
        self.total_reward += reward_for_invalid_move
        self.rewards_received.append(reward_for_invalid_move)
        return reward_for_invalid_move

    def move(self, move_type: str):
        """ Make a move and return reward for this move """
        player_row, player_col = self.get_player_position()
        old_game_state = np.copy(self.current_level)
        self.move_counter += 1
        self.moves_made.append(move_type.upper())
        if move_type.upper() == self.MOVE_UP.upper():
            if self.is_move_up_valid():
                self.move_internal(player_row, player_col, player_row - 1, player_col, player_row - 2, player_col)
                return self.get_reward_for_move(old_game_state)
            else:
                return self.handle_invalid_move(do_print_message=self.is_manual)
        elif move_type.upper() == self.MOVE_DOWN.upper():
            if self.is_move_down_valid():
                self.move_internal(player_row, player_col, player_row + 1, player_col, player_row + 2, player_col)
                return self.get_reward_for_move(old_game_state)
            else:
                return self.handle_invalid_move(do_print_message=self.is_manual)
        elif move_type.upper() == self.MOVE_LEFT.upper():
            if self.is_move_left_valid():
                self.move_internal(player_row, player_col, player_row, player_col - 1, player_row, player_col - 2)
                return self.get_reward_for_move(old_game_state)
            else:
                return self.handle_invalid_move(do_print_message=self.is_manual)
        elif move_type.upper() == self.MOVE_RIGHT.upper():
            if self.is_move_right_valid():
                self.move_internal(player_row, player_col, player_row, player_col + 1, player_row, player_col + 2)
                return self.get_reward_for_move(old_game_state)
            else:
                return self.handle_invalid_move(do_print_message=self.is_manual)
        else:
            print("     >>> ERROR: Unrecognized move type!")
            return 0

    # ------------------ game end handlers -------------------------------------------------------------------------------------------------------------------------------------
    def add_to_game_memory(self, reward, move_type):
        self.moves_made.append(move_type)
        self.rewards_received.append(reward)

    def save_game_memory_to_file(self, filename: str = "game_", file_extension: str = "txt", separator: str = ';'):
        """
        saves level name, moves and rewards received to file. Format: \n
        line 1: path to level file  \n
        line 2: moves made - separated by chosen separator (default ;) \n
        line 3: rewards received - separated by chosen separator (default ;) \n
        line 4: total reward received
        line 5: map rotation option - 0 = none, 1 - 90, 2 - 180, 3 - 270
        """
        map_name = self.path_to_current_level.split('/')[1].replace('.txt', '')     # map file name without extension assuming path_to_current_level is with directory
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')
        filename = self.PATH_TO_MANUAL_GAMES + map_name + "_" + filename + current_date + "." + file_extension

        moves_str = ""
        for move in self.moves_made:
            moves_str += move + separator
        moves_str = moves_str[:-1]  # remove final character

        rewards_str = ""
        for reward in self.rewards_received:
            rewards_str += str(reward) + separator
        rewards_str = rewards_str[:-1]  # remove final character

        with open(filename, "w+") as f:
            f.write(self.path_to_current_level + "\n")
            f.write(moves_str + "\n")
            f.write(rewards_str + "\n")
            f.write(str(self.total_reward) + "\n")
            f.write(str(self.map_rotation))

        return filename

    @staticmethod
    def get_game_from_file(file_name: str):
        with open(file_name, "r") as f:
            read_lines = f.readlines()

        # use rstrip() to remove new line characters at the end of strings read by f.readlines()
        map_name = read_lines[0].rstrip()
        moves = read_lines[1].rstrip()
        rewards = read_lines[2].rstrip()
        total_reward = read_lines[3].rstrip()
        if len(read_lines) > 4:
            map_rotation = read_lines[4].rstrip()
        else:   # if rotation not specified assume that there is no rotation
            map_rotation = SokobanGame.MAP_ROTATION_NONE

        return map_name, moves, rewards, total_reward, map_rotation

    def check_and_process_game_end(self, save_record_to_file: bool = True):
        """ To be called after making move, returns True if game is over, False if it is not and returns final reward - 0 if not game over yet  """
        is_victory, reward_for_victory = self.is_victory()
        is_loss, reward_for_loss = self.is_loss()
        if save_record_to_file:
            self.save_game_memory_to_file()
        if is_victory:
            if self.is_manual:
                self.save_game_memory_to_file()
            return True, reward_for_victory
        if is_loss:
            if self.is_manual:
                self.save_game_memory_to_file()
            return True, reward_for_loss
        else:
            return False, 0

    def add_reward_to_game_memory(self, reward: int):
        self.total_reward += reward
        self.rewards_received.append(reward)

    def is_victory(self, only_check: bool = False):
        remaining_boxes = (self.current_level == self.BOX).sum()
        if remaining_boxes == 0:
            reward_for_victory = self.reward_system.get_reward_for_victory()
            if not only_check:
                self.add_reward_to_game_memory(reward_for_victory)
            return True, reward_for_victory
        else:
            return False, 0

    def is_loss(self, only_check: bool = False):
        remaining_boxes = (self.current_level == self.BOX).sum()
        reward_for_loss = self.reward_system.get_reward_for_loss()
        if self.move_counter >= self.game_timeout and remaining_boxes > 0:
            if not only_check:
                self.add_reward_to_game_memory(reward_for_loss)
            return True, reward_for_loss
        elif self.is_at_least_one_box_blocked():
            if not only_check:
                self.add_reward_to_game_memory(reward_for_loss)
            return True, reward_for_loss
        else:
            return False, 0

    def is_at_least_one_box_blocked(self):
        boxes_positions = np.where(self.current_level == self.BOX)  # no need to check box_on_target, they can be blocked
        boxes_pos_rows = boxes_positions[0]
        boxes_pos_cols = boxes_positions[1]
        for ind in range(len(boxes_pos_rows)):
            if self.is_box_in_position_blocked(boxes_pos_rows[ind], boxes_pos_cols[ind]):
                return True
        return False

    def is_box_in_position_blocked(self, box_row: int, box_col: int):
        element_left = self.current_level[box_row, box_col - 1]
        element_right = self.current_level[box_row, box_col + 1]
        element_up = self.current_level[box_row - 1, box_col]
        element_down = self.current_level[box_row + 1, box_col]
        if (element_up == self.WALL or element_down == self.WALL) and (element_left == self.WALL or element_right == self.WALL):
            return True
        else:
            return False


class ManualPlaySokoban:
    key_pressed_event = threading.Event()
    user_input = ""
    exit_string = 'e'
    rules_string = 'r'

    def on_key_press(self, key):
        """ intercept keyboard key press and return the pressed key """
        try:
            pressed_key = key.char
            if pressed_key.upper() == SokobanGame.MOVE_UP.upper():
                self.user_input = SokobanGame.MOVE_UP.upper()
            if pressed_key.upper() == SokobanGame.MOVE_DOWN.upper():
                self.user_input = SokobanGame.MOVE_DOWN.upper()
            if pressed_key.upper() == SokobanGame.MOVE_LEFT.upper():
                self.user_input = SokobanGame.MOVE_LEFT.upper()
            if pressed_key.upper() == SokobanGame.MOVE_RIGHT.upper():
                self.user_input = SokobanGame.MOVE_RIGHT.upper()
            if pressed_key.upper() == self.exit_string.upper():
                self.user_input = self.exit_string
            if pressed_key.upper() == self.rules_string.upper():
                self.user_input = self.rules_string
            else:
                self.user_input = key.char
            self.key_pressed_event.set()
        except AttributeError:
            pass

    def sokoban_manual_play(self, level_name: str = SokobanGame.PATH_TO_LEVELS + "simple_level_2.txt", use_wsad: bool = False, map_rotation: int = 0):
        if use_wsad:
            SokobanGame.change_controls()
        rew_impl = RewardSystem()
        game = SokobanGame(level_name, rew_impl, loss_timeout=SokobanGame.DEFAULT_TIMEOUT, manual_play=True,
                           map_rotation=map_rotation)
        continue_game = True
        SokobanGame.print_rules()
        print("Use 'e' to end the game, 'r' to print game rules")
        allowed_moves = [SokobanGame.MOVE_LEFT.upper(), SokobanGame.MOVE_RIGHT.upper(), SokobanGame.MOVE_UP.upper(), SokobanGame.MOVE_DOWN.upper()]
        allowed_moves_str = "("
        for m in allowed_moves:
            allowed_moves_str += m + ','
        allowed_moves_str = allowed_moves_str[:-1]      # remove final character
        allowed_moves_str += ")"

        print("Using key press events, no need to confirm symbols with Enter")
        print("Press any key to process it - ", allowed_moves_str, "for moves,", self.exit_string, "for exit",
              self.rules_string, "for rules")
        time.sleep(1)
        with keyboard.Listener(on_press=self.on_key_press) as listener:     # comment this if you want key + enter instead of keyboard listener
            while continue_game:
                os.system('cls')
                game.print_current_level()
                print("Are moves valid:")
                print("up:", game.is_move_up_valid(), ", ", end='')
                print("down:", game.is_move_down_valid(), ", ", end='')
                print("left:", game.is_move_left_valid(), ", ", end='')
                print("right:", game.is_move_right_valid(), end='')
                print("")
                print("What move do you want to make? " + allowed_moves_str)

                # user_input = input()       # uncomment this and comment below 2 lines for key + enter instead of keyboard listener
                self.key_pressed_event.wait()
                self.key_pressed_event.clear()

                if self.user_input.upper() in allowed_moves:
                    # two lines of actual game processing
                    reward = game.move(self.user_input)
                    game.check_and_process_game_end(save_record_to_file=False)

                    # informational prints
                    is_v, rv = game.is_victory(only_check=True)
                    is_l, rl = game.is_loss(only_check=True)
                    if is_v:
                        print("+++ YOU WON! +++")
                        print("Exiting...")
                        continue_game = False
                        reward = rv
                    if is_l:
                        print("--- YOU LOST! ---")
                        print("Exiting...")
                        continue_game = False
                        reward = rl
                    print("Victory:", is_v, "| Loss:", is_l, "| Moves made:", game.move_counter, "/", game.game_timeout,
                          "| Reward for this move:", reward, "| Total reward: ", game.total_reward)
                elif self.user_input.upper() == self.exit_string.upper():
                    print("Exiting...")
                    continue_game = False
                elif self.user_input.upper() == self.rules_string.upper():
                    SokobanGame.print_rules()
                else:
                    print("     >>> ERROR: Unrecognized move or command!")


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-m", "--map", type=str,
                             help="path to map, eg 'non_rectangle_level.txt', levels directory is already specified internally",
                             dest="map", default="SIMPLE_non_rectangle_level.txt")
    args_parser.add_argument("-r", "--rotation", type=int,
                             help="rotation of map: 0 - none, 1- 90 degrees, 2 - 180 degrees, 3 - 270 degrees, -1 fliplr, -2 flipud",
                             choices=SokobanGame.ROTATIONS_ALL, dest="rotation", default=0)
    args_parser.add_argument("-w", "--wasd", help="change controls to WASD instead of using default LRUD", action="store_true",
                             dest="use_wasd")
    args = args_parser.parse_args()

    level_path = SokobanGame.PATH_TO_LEVELS
    level_path += args.map
    chosen_rotation = args.rotation
    do_use_wasd = args.use_wasd

    manual_sokoban = ManualPlaySokoban()
    manual_sokoban.sokoban_manual_play(level_path, use_wsad=do_use_wasd, map_rotation=chosen_rotation)

    # generate_map()
