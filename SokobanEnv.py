import os
import gc
import random
import datetime
import numpy as np
from rl.core import Env
from SokobanGame import SokobanGame
from SokobanGame import RewardSystem
from gym.spaces.discrete import Discrete
from gym.spaces import Box


# https://github.com/mpSchrader/gym-sokoban/blob/master/gym_sokoban/envs/sokoban_env.py
# https://github.com/jakegrigsby/AdvancedPacmanDQNs/tree/master/agents
# https://github.com/keras-rl/keras-rl/blob/master/rl/core.py
# https://github.com/keras-rl/keras-rl/blob/master/rl/callbacks.py
# https://github.com/keras-rl/keras-rl/blob/master/rl/policy.py
# https://github.com/keras-rl/keras-rl/blob/master/rl/agents/dqn.py
# https://github.com/MartinThoma/banana-gym/blob/master/gym_banana/envs/banana_env.py
# https://github.com/openai/gym-soccer/blob/master/gym_soccer/envs/soccer_empty_goal.py
# https://github.com/openai/gym/tree/master/gym/spaces

class SokobanEnv(Env):
    GAME_SIZE_ROWS = 32
    GAME_SIZE_COLS = 32

    PATH_TO_GAME_STATS = 'game_stats/'

    ENV_DTYPE = 'float32'

    USE_ONLY_SIMPLE_AND_VERY_SIMPLE_MAPS = 0
    USE_ALL_MAPS_ALWAYS = 1
    USE_MAPS_DIFFICULTY_LEVEL = 2

    # TODO: maybe these dicts need adjusting?
    ACTIONS = {
        0: SokobanGame.MOVE_LEFT,
        1: SokobanGame.MOVE_RIGHT,
        2: SokobanGame.MOVE_UP,
        3: SokobanGame.MOVE_DOWN
    }

    SOKOBAN_SYMBOLS_MAPPING = {
        SokobanGame.WALL            : 0,
        SokobanGame.FREE_SPACE      : 1,
        SokobanGame.BOX             : 3,
        SokobanGame.TARGET          : 5,
        SokobanGame.BOX_ON_TARGET   : 6,
        SokobanGame.PLAYER          : 8,
        SokobanGame.PLAYER_ON_TARGET: 9
    }

    GAMES_COUNT_AND_MAP_PREFIXES = [
        (0, "VERY_SIMPLE"),
        (500, "SIMPLE"),
        (2500, "MEDIUM"),
        (5000, "HARD"),
        (10000, "VERY_HARD")
    ]

    ENV_STATE_INIT_VALUE = -999.0

    reward_range = (RewardSystem.get_reward_for_loss(), RewardSystem.get_reward_for_victory())

    env_game_state = None
    available_maps = []     # paths to maps
    available_map_rotations = [SokobanGame.MAP_ROTATION_NONE, SokobanGame.MAP_ROTATION_90, SokobanGame.MAP_ROTATION_180, SokobanGame.MAP_ROTATION_270]

    sokoban_game = None     # SokobanGame object
    game_timeout = 0
    map_in_the_center_of_fixed_size_matrix = True

    print_info_game_count = 0
    games_counter = 0
    victory_counter = 0
    temp_victory_counter = 0

    enable_debug_printing = False
    use_bugged_dict_entries = True

    map_frequency_stats = {}
    map_frequency_victory_stats = {}
    game_stats = []
    save_file_name = ""
    save_every_game_to_file = False
    use_map_difficulty_in_training_option = 0
    current_level_name = ""

    def __init__(self, game_timeout: int = SokobanGame.DEFAULT_TIMEOUT, put_map_in_the_center: bool = True,
                 info_game_count: int = 1000, enable_debug_printing: bool = False, use_bugged_dict_entries: bool = True,
                 save_file_name: str = 'basicDQN_game_', save_every_game_to_file: bool = False,
                 map_choice_option=0):
        """ Default env size is 32x32.
        Map choice options: \n
        USE_ONLY_SIMPLE_AND_VERY_SIMPLE_MAPS = 0 (default)\n
        USE_ALL_MAPS_ALWAYS = 1  - does not filter maps by difficulty, could be used to test trained models \n
        USE_MAPS_DIFFICULTY_LEVEL = 2  - will use SokobanEnv.GAMES_COUNT_AND_MAP_PREFIXES to determine when to use which maps
        """
        self.env_game_state = self.generate_fixed_size_map_with_default_values()
        self.available_maps = self.get_all_available_maps()
        self.game_timeout = game_timeout
        self.map_in_the_center_of_fixed_size_matrix = put_map_in_the_center
        self.print_info_game_count = info_game_count
        self.enable_debug_printing = enable_debug_printing
        self.use_bugged_dict_entries = use_bugged_dict_entries
        self.save_file_name = save_file_name
        self.save_every_game_to_file = save_every_game_to_file
        self.use_map_difficulty_in_training_option = map_choice_option

        # TODO: is Env.action_space and Env.observation.space needed?
        # below commented code is modelled on https://github.com/mpSchrader/gym-sokoban/blob/master/gym_sokoban/envs/sokoban_env.py
        # self.action_space = Discrete(len(self.ACTIONS))
        # max_value_in_symbols = max(self.SOKOBAN_SYMBOLS_MAPPING.values())
        # min_value_in_symbols = min(self.SOKOBAN_SYMBOLS_MAPPING.values())
        # self.observation_space = Box(low=min_value_in_symbols, high=max_value_in_symbols, shape=(self.GAME_SIZE_ROWS, self.GAME_SIZE_COLS), dtype=self.ENV_DTYPE)

        # load first map
        self.reset()

    @staticmethod
    def get_all_available_maps():
        found_maps = []
        for file in os.listdir(SokobanGame.PATH_TO_LEVELS):
            if file.endswith(".txt"):
                found_maps.append(file)
        return found_maps

    @staticmethod
    def get_maps_with_prefix(prefix):
        found_maps = []
        for file in os.listdir(SokobanGame.PATH_TO_LEVELS):
            if file.endswith(".txt"):
                if file.upper().startswith(prefix.upper()):  # check all with available prefixes
                    found_maps.append(file)
        return found_maps

    @staticmethod
    def generate_fixed_size_map_with_default_values():
        return np.full(shape=(SokobanEnv.GAME_SIZE_ROWS, SokobanEnv.GAME_SIZE_COLS),
                       fill_value=SokobanEnv.ENV_STATE_INIT_VALUE,
                       dtype=SokobanEnv.ENV_DTYPE)

    @staticmethod
    def convert_map_to_fixed_size(map_to_convert, put_map_in_the_center: bool = True):
        converted_map = SokobanEnv.generate_fixed_size_map_with_default_values()
        map_rows, map_cols = np.shape(map_to_convert)
        map_copy = np.zeros(shape=(map_rows, map_cols)).astype(SokobanEnv.ENV_DTYPE)  # prepare matrix with size of map but with numbers instead of chars
        original_sokoban_elements = [SokobanGame.WALL, SokobanGame.FREE_SPACE, SokobanGame.BOX, SokobanGame.TARGET,
                                     SokobanGame.BOX_ON_TARGET, SokobanGame.PLAYER, SokobanGame.PLAYER_ON_TARGET]
        # replace chars with numbers
        for symbol in original_sokoban_elements:
            map_copy[map_to_convert == symbol] = SokobanEnv.SOKOBAN_SYMBOLS_MAPPING[symbol]
        if put_map_in_the_center:
            row_middle_of_fixed_size_matrix = int(SokobanEnv.GAME_SIZE_ROWS / 2)
            col_middle_of_fixed_size_matrix = int(SokobanEnv.GAME_SIZE_COLS / 2)
            row_begin = row_middle_of_fixed_size_matrix - int(map_rows / 2)
            col_begin = col_middle_of_fixed_size_matrix - int(map_cols / 2)
        else:
            row_begin = 0
            col_begin = 0
        # paste map into larger matrix of fixed size
        converted_map[row_begin: row_begin + map_rows, col_begin: col_begin + map_cols] = map_copy
        # replace surrounding space with walls
        converted_map[converted_map == SokobanEnv.ENV_STATE_INIT_VALUE] = SokobanEnv.SOKOBAN_SYMBOLS_MAPPING[SokobanGame.WALL]
        return converted_map

    @staticmethod
    def print_matrix(mat):
        print("-" * 20)
        for row in mat:
            for col in row:
                print(col, end=' ')
            print("")

    @staticmethod
    def configure_env_size(new_rows: int, new_cols: int):
        SokobanEnv.GAME_SIZE_ROWS = new_rows
        SokobanEnv.GAME_SIZE_COLS = new_cols

    @staticmethod
    def configure_difficulty_games_count_requirement(simple_threshold: int, medium_threshold: int, hard_threshold, very_hard_threshold: int):
        """ Threshold for very simple maps is always 0 """
        SokobanEnv.GAMES_COUNT_AND_MAP_PREFIXES = [
            (0, "VERY_SIMPLE"),
            (simple_threshold, "SIMPLE"),
            (medium_threshold, "MEDIUM"),
            (hard_threshold, "HARD"),
            (very_hard_threshold, "VERY_HARD")
        ]

    def print_env(self, numbers_to_symbols: bool = False):
        for row in self.env_game_state:
            for col in row:
                prt = col
                if numbers_to_symbols:
                    prt = list(SokobanEnv.SOKOBAN_SYMBOLS_MAPPING.keys())[list(SokobanEnv.SOKOBAN_SYMBOLS_MAPPING.values()).index(int(col))]
                print(prt, end='')
            print("")

    def configure(self, *args, **kwargs):
        # do nothing
        pass

    def update_env_state(self):
        """ converts loaded game map to fixed size """
        self.env_game_state = self.convert_map_to_fixed_size(self.sokoban_game.current_level,
                                                             put_map_in_the_center=self.map_in_the_center_of_fixed_size_matrix)

    def print_games_won_info_if_needed(self, save_current_game_to_file: bool = True):
        """ Simple basic logging \n
        True indicates that game was saved to file, False that it wasn't """
        if self.games_counter % self.print_info_game_count == 0:
            print("")
            print(" >>>>>>> " + str(self.victory_counter) + "/" + str(self.games_counter) + " games won")
            print(" >>>>>>> " + str(self.temp_victory_counter) + "/" + str(self.print_info_game_count) + " games won in this logging period")
            print(" >>>>>>> number of maps for training: " + str(len(self.available_maps)))
            self.temp_victory_counter = 0
            if save_current_game_to_file:
                self.save_game_to_file(print_save_message=True)
                return True
            else:
                return False
        else:
            return False

    def get_available_maps_with_difficulty(self):
        """ difficulty according to SokobanEnv.GAMES_COUNT_AND_MAP_PREFIXES """
        found_maps = []
        available_prefixes = []
        games_played_count_ind = 0
        map_name_prefix_ind = 1
        # first get available prefixes
        for count_prefix in self.GAMES_COUNT_AND_MAP_PREFIXES:
            if count_prefix[games_played_count_ind] <= self.games_counter:
                available_prefixes.append(count_prefix[map_name_prefix_ind])
        # then maps with these prefixes
        for prefix in available_prefixes:
            maps = self.get_maps_with_prefix(prefix)
            found_maps.extend(maps)
        return found_maps

    # ------------------ necessary overrides of base Env --------------------------------------------------------------------------------------------------------------------------------

    def step(self, action):
        """
        Run one timestep of the environment's dynamics.
        Accepts an action and returns a tuple (observation, reward, done, info).
        # Arguments
            action (object): An action provided by the environment.
        # Returns
            observation (object): Agent's observation of the current environment.
            reward (float) : Amount of reward returned after previous action.
            done (boolean): Whether the episode has ended, in which case further step() calls will return undefined results.
            info (dict): Contains auxiliary diagnostic information (helpful for debugging, and sometimes learning).
        """
        if action not in self.ACTIONS:
            raise ValueError("Action " + str(action) + " not in available actions!")

        sokoban_action = self.ACTIONS[action]   # action in form ready for SokobanGame object, action parameter is in numeric form, we need to convert it

        reward_for_this_step = self.sokoban_game.move(sokoban_action)
        game_done, reward_for_game_end = self.sokoban_game.check_and_process_game_end(save_record_to_file=False)
        step_info_dict = {
            "action_taken": sokoban_action,
            "level_name": self.get_current_level_name(),
            "level_rotation_option": self.get_current_level_rotation()
        }
        if game_done:
            reward_for_this_step = reward_for_game_end

            was_victory, _ = self.sokoban_game.is_victory(only_check=True)
            self.add_game_stats_entry(was_victory=was_victory)

            if was_victory:     # for stats
                self.victory_counter += 1
                self.temp_victory_counter += 1
                # add map victory stats
                self.add_one_to_stats_dict(stats_dict=self.map_frequency_victory_stats, key=self.current_level_name)
            if self.use_bugged_dict_entries:
                step_info_dict["moves_count"] = self.sokoban_game.move_counter  # this appears to sometimes cause error in keras-rl callback logger - see BasicDQN.py for quick fix
                step_info_dict["was_victory"] = was_victory

            if self.enable_debug_printing:
                self.debug_print("game over , was victory: " + str(was_victory) + " num of moves made: " + str(self.sokoban_game.move_counter))
        self.update_env_state()

        return self.get_env_for_keras(), reward_for_this_step, game_done, step_info_dict

    def reset(self):
        """
        Resets the state of the environment and returns an initial observation. \n
        # Returns
            observation (object): The initial observation of the space. Initial reward is assumed to be 0.
        """
        # simple logging of victory stats before we reset the env
        self.games_counter += 1
        game_was_saved_to_file = self.print_games_won_info_if_needed()
        if (not game_was_saved_to_file) and self.save_every_game_to_file:   # if we want to save every game played by agent to separate file
            self.save_game_to_file(print_save_message=False)

        # get available maps - according to map selection option defined when creating the env object
        if self.use_map_difficulty_in_training_option == self.USE_MAPS_DIFFICULTY_LEVEL:
            self.available_maps = self.get_available_maps_with_difficulty()
        elif self.use_map_difficulty_in_training_option == self.USE_ALL_MAPS_ALWAYS:
            self.available_maps = self.get_all_available_maps()
        else:   # default
            self.available_maps = self.get_maps_with_prefix("VERY_SIMPLE")
            self.available_maps.extend(self.get_maps_with_prefix("SIMPLE"))

        # choose random map from available ones
        chosen_map = SokobanGame.PATH_TO_LEVELS + random.choice(self.available_maps)
        self.current_level_name = chosen_map
        self.add_one_to_stats_dict(stats_dict=self.map_frequency_stats, key=self.current_level_name)
        chosen_rotation = random.choice(self.available_map_rotations)

        # create SokobanGame object
        rew_impl = RewardSystem()
        self.sokoban_game = SokobanGame(chosen_map, rew_impl,
                                        loss_timeout=self.game_timeout,
                                        manual_play=False,
                                        map_rotation=chosen_rotation)

        if self.enable_debug_printing:
            self.debug_print("Reset method call")

        # check map dimensions
        level_size_rows, level_size_cols = np.shape(self.sokoban_game.current_level)
        if level_size_rows > self.GAME_SIZE_ROWS or level_size_cols > self.GAME_SIZE_COLS:
            raise ValueError("map size after rotation too large! Used map " + str(chosen_map) + " and rotation " + str(chosen_rotation))
        # make map of fixed size - prepare loaded map
        self.update_env_state()

        return self.get_env_for_keras()     # return map in state ready for keras

    def render(self, mode='human', close=False):
        """
        Renders the environment.
        The set of supported modes varies per environment. (And some
        environments do not support rendering at all.)
        # Arguments
            mode (str): The mode to render with.
            close (bool): Close all open renderings.
        """
        if mode == 'human':
            self.sokoban_game.print_current_level()
        else:
            pass

    def close(self):
        """
        Override in your subclass to perform any necessary cleanup.
        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        gc.collect()    # just to be sure...
        pass

    def seed(self, seed=None):
        """
        Sets the seed for this env's random number generator(s).
        # Returns
            Returns the list of seeds used in this env's random number generators
        """
        # TODO: what here?
        pass

    def get_env_for_keras(self):
        """ Used to return game_env in form ready for keras CNN
         keras Conv2D requires channels even if there aren't any so we must reshape env from (64,64) to (64,64,1) \n
         If we want another format (eg. additional representation of game map in additional channels) this method needs to be changed"""
        #return self.env_game_state                                                                 # for Conv1D
        return np.expand_dims(self.env_game_state, axis=2)                                          # for Conv2D

    # ------------------ stats utils --------------------------------------------------------------------------------------------------------------------------------

    def get_current_level_name(self):
        return self.sokoban_game.path_to_current_level

    def get_current_level_rotation(self):
        return self.sokoban_game.map_rotation

    def debug_print(self, communicate: str, print_current_map: bool = True):
        print("")   # print empty line to make communicate more visible
        print(">>>> [DEBUG] " + communicate)
        if print_current_map:
            self.sokoban_game.print_current_level()

    def print_map_victory_stats(self):
        print("Map victory statistics: [map - victories/played games]")
        for used_map in self.map_frequency_stats:
            stats_for_used_map = self.get_map_stats_line_for_key(used_map)
            print(stats_for_used_map)

    def add_game_stats_entry(self, was_victory: bool):
        """ Data format: level name, map rotation, bool - was victory, number of moves, total reward """
        self.game_stats.append(
            (self.get_current_level_name(), self.get_current_level_rotation(), was_victory,
             self.sokoban_game.move_counter, self.sokoban_game.total_reward)
        )

    def save_game_stats_to_file(self, base_name: str, delimiter: str = ';', file_extension='.txt'):
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = self.PATH_TO_GAME_STATS + "game_stats_" + base_name + "_" + current_date + file_extension
        summary_filename = self.PATH_TO_GAME_STATS + "game_stats_summary_" + base_name + "_" + current_date + file_extension
        with open(filename, 'w+') as f:
            for line in self.game_stats:
                line_to_file = ""
                for el in line:
                    line_to_file += str(el) + delimiter
                line_to_file = line_to_file[:-1]    # remove last element in line - delimiter
                f.write(line_to_file + '\n')
        with open(summary_filename, 'w+') as f:  # save stats summary
            for used_map in self.map_frequency_stats:
                stats_for_used_map = self.get_map_stats_line_for_key(used_map)
                f.write(stats_for_used_map + '\n')
        return filename, summary_filename

    def save_game_to_file(self, print_save_message: bool = False):
        file_name = self.sokoban_game.save_game_memory_to_file(filename=self.save_file_name)
        if print_save_message:
            print("Saving current game to file: " + file_name)

    def get_map_stats_line_for_key(self, key):
        """ Format: map name - games won/games played """
        try:
            games_won = str(self.map_frequency_victory_stats[key])
        except KeyError:  # indicates that there were no victories on given map
            games_won = 0
        return str(key + " - " + str(games_won) + "/" + str(self.map_frequency_stats[key]))

    @staticmethod
    def add_one_to_stats_dict(stats_dict, key):
        if key in stats_dict:
            stats_dict[key] += 1
        else:
            stats_dict[key] = 1


if __name__ == "__main__":
    print("Simple test: get level and make one step")
    e = SokobanEnv()
    print("Level and rotation: ", e.get_current_level_name(), e.get_current_level_rotation())
    print("The level:")
    e.print_env(numbers_to_symbols=True)
    obs, rew, fin, info = e.step(0)
    print("Step returned: ", rew, fin, info)
    print("The level after step:")
    e.print_env(numbers_to_symbols=True)
