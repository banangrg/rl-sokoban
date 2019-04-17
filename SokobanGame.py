import sys
import datetime
import threading
import numpy as np
from pynput import keyboard


# # - wall
# SPACE - free space
# $ - box
# . - target for boxes
# * - box on target
# @ - player
# + - player on target


class AbstractRewardSystem:
    def get_reward_for_move(self):
        raise NotImplementedError("Please Implement this method")

    def get_reward_for_box_on_target(self):
        raise NotImplementedError("Please Implement this method")

    def get_reward_for_box_off_target(self):
        raise NotImplementedError("Please Implement this method")

    def get_reward_for_invalid_move(self):
        raise NotImplementedError("Please Implement this method")

    def get_reward_for_victory(self):
        raise NotImplementedError("Please Implement this method")

    def get_reward_for_loss(self):
        raise NotImplementedError("Please Implement this method")


class RewardSystem(AbstractRewardSystem):
    def get_reward_for_move(self):
        """ for move without any effect """
        return -0.05

    def get_reward_for_box_on_target(self):
        return 8.0

    def get_reward_for_box_off_target(self):
        return -8.0

    def get_reward_for_invalid_move(self):
        return -3.0

    def get_reward_for_victory(self):
        return 30.0

    def get_reward_for_loss(self):
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

    PATH_TO_LEVELS = 'levels/'
    PATH_TO_MANUAL_GAMES = 'manual_games/'

    # instance variables
    current_level = None
    reward_system = None
    move_counter = 0
    total_reward = 0.0
    moves_made = []
    rewards_received = []
    game_timeout = None
    path_to_current_level = None
    is_manual = None
    map_rotation = None

    def __init__(self, path_to_level: str, reward_impl: AbstractRewardSystem, loss_timeout: int = DEFAULT_TIMEOUT,
                 manual_play: bool = True, map_rotation: int = MAP_ROTATION_NONE):
        """ Initializes single game. Requires path to file with level and a reward system (ex. basic RewardSystem()).
            Does basic validation of loaded level."""
        self.load_level(path_to_level)
        validation_ok, reason = self.check_loaded_level_basic_validation()
        if not validation_ok:
            raise Exception(reason)
        if not isinstance(reward_impl, AbstractRewardSystem):
            raise Exception("Invalid reward system")
        self.reward_system = reward_impl
        self.game_timeout = loss_timeout
        self.path_to_current_level = path_to_level
        self.is_manual = manual_play
        if map_rotation not in [self.MAP_ROTATION_NONE, self.MAP_ROTATION_90, self.MAP_ROTATION_180, self.MAP_ROTATION_270]:
            raise Exception("Invalid map rotation option!")
        self.map_rotation = map_rotation
        # rotate map according to setting
        self.current_level = np.rot90(self.current_level, k=map_rotation)

    @staticmethod
    def get_level(filepath: str):
        """ Gets level with specified path as numpy array of characters, does NOT check map validity """
        with open(filepath, "r") as f:
            lines = f.readlines()
        lines = [line.rstrip('\r\n') for line in lines]
        characters = []
        for line in lines:
            chars_line = []
            chars_line.extend(line)
            characters.append(chars_line)
        return np.array(characters)

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
                ", targets: " + target_count
            print(reason)
            return False, reason
        if player_count != 1:
            reason = "VALIDATION FAILED: Number of players != 1, actual: " + str(player_count)
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
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.PATH_TO_MANUAL_GAMES + filename + current_date + "." + file_extension

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

    def check_and_process_game_end(self):
        """ To be called after making move, returns True if game is over, False if it is not and returns final reward - 0 if not game over yet  """
        is_victory, reward_for_victory = self.is_victory()
        is_loss, reward_for_loss = self.is_loss()
        if is_victory:
            self.save_game_memory_to_file()
            return True, reward_for_victory
        if is_loss:
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
        print("Use 'exit' to end the game, 'rules' to print game rules")
        allowed_moves = [SokobanGame.MOVE_LEFT.upper(), SokobanGame.MOVE_RIGHT.upper(), SokobanGame.MOVE_UP.upper(), SokobanGame.MOVE_DOWN.upper()]
        allowed_moves_str = "("
        for m in allowed_moves:
            allowed_moves_str += m + ','
        allowed_moves_str = allowed_moves_str[:-1]      # remove final character
        allowed_moves_str += ")"

        print("Using key press events, no need to confirm symbols with Enter")
        print("Press any key to process it - ", allowed_moves_str, "for moves,", self.exit_string, "for exit",
              self.rules_string, "for rules")
        with keyboard.Listener(on_press=self.on_key_press) as listener:     # comment this if you want key + enter instead of keyboard listener
            while continue_game:
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
                    game.check_and_process_game_end()

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
    level_path = SokobanGame.PATH_TO_LEVELS
    if len(sys.argv) > 1:
        level_path += sys.argv[1]
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print("First argument is name of file with level, path to levels directory is already present. Example cmd: python SokobanGame.py simplest_possible_level.txt")
            sys.exit(0)
    else:
        level_path += "simple_level_3.txt"
    manual_sokoban = ManualPlaySokoban()
    manual_sokoban.sokoban_manual_play(level_path, use_wsad=True, map_rotation=SokobanGame.MAP_ROTATION_NONE)
