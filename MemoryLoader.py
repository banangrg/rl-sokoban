import os
import sys
from rl.memory import Memory
from SokobanEnv import SokobanEnv
from SokobanGame import SokobanGame


class SokobanManualGameMemoryLoader:
    DEFAULT_PATH_TO_GAMES = 'manual_games_to_load/'
    MOVE_SEPARATOR = ';'
    PRINT_LIMITER = 10000  # once this many steps message will be printed

    def __init__(self, agent_memory: Memory, memory_limit: int, path_to_games: str = DEFAULT_PATH_TO_GAMES,
                 is_map_in_center: bool = True, do_scale_rewards: bool = False, do_scale_env: bool = False):
        """ memory_linit means how many moves you want to load into agent memory """
        self.agent_memory = agent_memory
        self.memory_limit = memory_limit
        self.path_to_games = path_to_games
        self.is_map_in_center = is_map_in_center
        self.do_scale_rewards = do_scale_rewards
        self.do_scale_env = do_scale_env

    def get_env_for_current_file(self, map_name: str, map_rotation: int):
        env = SokobanEnv(
            game_timeout=SokobanGame.DEFAULT_TIMEOUT,
            put_map_in_the_center=self.is_map_in_center,
            info_game_count=500,    # this will never be used in this case
            use_bugged_dict_entries=False,
            save_file_name='test_DQN_game_',    # this will never be used in this case
            save_every_game_to_file=False,  # it would be pointless to save already saved game...
            map_choice_option=SokobanEnv.USE_SINGLE_SPECIFIED_MAP,
            use_more_than_one_channel=False,    # current implementation does NOT support window_length != 1
            scale_rewards=self.do_scale_rewards,
            scale_range=(-1, 1),
            use_scaled_env_representation=self.do_scale_env,
            disable_map_rotation=False,     # has to be false because we manually set rotation
            specific_map=map_name,
            use_specific_rotation=True,     # we must specify rotation from file
            specific_rotation=map_rotation
        )

        return env

    def load_all_games(self):
        move_counter = 0
        print_counter = 0
        is_memory_full = False

        # load moves into agents memory until specified limit is reached
        while not is_memory_full:
            for file in os.listdir(self.path_to_games):
                if print_counter >= self.PRINT_LIMITER or print_counter == 0:
                    print('Loading file ' + file + ', move counter = ' + str(move_counter) + '/' + str(self.memory_limit))
                    print_counter = 0
                map_name, moves, _, _, map_rotation = SokobanGame.get_game_from_file(self.path_to_games + file)

                str_rotations_all = [str(rot) for rot in SokobanGame.ROTATIONS_ALL]
                if map_rotation not in str_rotations_all:
                    print("Invalid map rotation! - " + str(map_rotation) + " in file " + file + " - skipping")
                    continue
                map_rotation = int(map_rotation)
                map_name = map_name.split('/')[1]   # extract only map name without 'levels/'

                try:
                    # prepare env
                    sokoban_env_for_this_game = self.get_env_for_current_file(map_name, map_rotation)
                    env_for_current_move = sokoban_env_for_this_game.reset()    # get first env state

                    # process every move from file
                    move_list = moves.split(self.MOVE_SEPARATOR)

                    # check if move can be translated to env representation
                    for move in move_list:
                        if move not in SokobanEnv.WASD_TO_ACTIONS and move not in SokobanEnv.LRUD_TO_ACTIONS:
                            print("Invalid move: " + str(move) + " file: " + file + " - skipping file")
                            continue

                    for move in move_list:
                        # check if memory is full - it would be a waste of time to continue loading when memory is already full
                        move_counter += 1
                        print_counter += 1
                        if move_counter == self.memory_limit:
                            is_memory_full = True
                            break

                        # first translate action to numerical one used by env step(...) method
                        if move in SokobanEnv.WASD_TO_ACTIONS:
                            env_move = SokobanEnv.WASD_TO_ACTIONS[move]
                        elif move in SokobanEnv.LRUD_TO_ACTIONS:
                            env_move = SokobanEnv.LRUD_TO_ACTIONS[move]

                        # process step with env
                        env_state, reward_for_this_step, game_done, step_info_dict = sokoban_env_for_this_game.step(env_move)

                        # append move to agents memory
                        # according to Memory of keras-rl:
                        # "This needs to be understood as follows: in `observation`, take `action`, obtain `reward`
                        # and weather the next state is `terminal` or not."
                        # and:
                        # "This is to be understood as a transition: Given `state0`, performing `action`
                        # yields `reward` and results in `state1`, which might be `terminal`."
                        # So we need to append state before the move was made and later replace the old move with the one returned by env.step(...)

                        # But in Memory.append(...) comment documentation there is:
                        # "observation (dict): Observation returned by environment
                        # action (int): Action taken to obtain this observation
                        # reward (float): Reward obtained by taking this action
                        # terminal (boolean): Is the state terminal"
                        # So this can be wrong...
                        self.agent_memory.append(env_for_current_move, env_move, reward_for_this_step, game_done, training=True)
                        env_for_current_move = env_state

                        if game_done:
                            break

                except ValueError:
                    print("Invalid map specified in file " + file + ' - skipping')
                    continue

                if is_memory_full:
                    print("Done loading! Loaded " + str(move_counter) + " moves to agent memory")
                    break
