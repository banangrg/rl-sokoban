import sys
import time
import numpy as np
from keras.models import Sequential
from keras.layers import Flatten, Conv2D, Dense, MaxPooling2D, Dropout, Conv1D, MaxPooling1D
from keras.optimizers import Adam
from rl.agents.dqn import DQNAgent
from rl.policy import EpsGreedyQPolicy, LinearAnnealedPolicy
from rl.memory import SequentialMemory
from rl.callbacks import TrainEpisodeLogger, ModelIntervalCheckpoint
from SokobanEnv import SokobanEnv
from SokobanGame import SokobanGame
from DQNAgentUtils import DimensionKillerProcessor
from DQNAgentUtils import save_agent_weights_and_summary_to_file
from DQNAgentUtils import show_reward_plot


# TODO: IMPORTANT!!! Sometomes there is some KeyError inside keras-rl. Use this as workaround
# add try-except KeyError in C:\Users\user\AppData\Local\Programs\Python\Python36\Lib\site-packages\rl\callbacks.py
# around 279 line
#try:
#    if len(self.info_names) > 0:
#        self.infos.append([logs['info'][k] for k in self.info_names])
#except KeyError:
#    print("Caught error in logging - trying to continue")


BASE_WEIGHTS_FILE_NAME = "test_basic_dqn"

NUMBER_OF_POSSIBLE_ACTIONS = 4
TOTAL_NUMBER_OF_STEPS = 10**6   # basic minimum is said to be 10 000 000
WINDOW_LENGTH = 1   # we dont need to have sense of directional heading and speed in Sokoban
VERBOSITY_LEVEL = 1
AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS = 500

ENV_SIZE_ROWS = 32
ENV_SIZE_COLS = 32

VERBOSITY_1_LOGGER_INTERVAL = 10000

CONV_LAYER_DIMENSION = 2    # to use Conv2d or Conv1D


if __name__ == "__main__":
    start_time = time.time()
    print("Basic DQN Agent to test if SokobanEnv is working")

    SokobanEnv.configure_env_size(new_rows=ENV_SIZE_ROWS, new_cols=ENV_SIZE_COLS)
    env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT,
                     put_map_in_the_center=True,
                     info_game_count=AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS,
                     use_bugged_dict_entries=False,
                     save_file_name='basicDQN_game_',
                     save_every_game_to_file=False,
                     map_choice_option=SokobanEnv.USE_MAPS_DIFFICULTY_LEVEL,
                     use_more_than_one_channel=False,
                     scale_rewards=False,
                     scale_range=(-1, 1),
                     use_scaled_env_representation=False,
                     disable_map_rotation=False)

    print("[INFO] Building model...")
    print("Environment size is: rows: " + str(env.GAME_SIZE_ROWS) + " cols: " + str(env.GAME_SIZE_COLS))
    input_rows = SokobanEnv.GAME_SIZE_ROWS
    input_cols = SokobanEnv.GAME_SIZE_COLS

    # TODO: maybe MaxPoolingND and Dropout not necessary? Or modify other params?
    if CONV_LAYER_DIMENSION == 1:
        model = Sequential()
        model.add(Conv1D(int(input_rows / 2), kernel_size=4, activation='relu', input_shape=(WINDOW_LENGTH, input_rows, input_cols), data_format='channels_first'))
        model.add(MaxPooling1D(pool_size=2))

        model.add(Conv1D(input_rows, kernel_size=3, activation='relu', data_format='channels_first'))
        model.add(MaxPooling1D(pool_size=2))

        model.add(Conv1D(input_rows, kernel_size=3, activation='relu', data_format='channels_first'))
        model.add(MaxPooling1D(pool_size=2))

        model.add(Flatten())
        model.add(Dense(512, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(NUMBER_OF_POSSIBLE_ACTIONS, activation='linear'))
    elif CONV_LAYER_DIMENSION == 2:
        model = Sequential()
        model.add(Conv2D(int(input_rows / 2), kernel_size=(4, 4), activation='relu',input_shape=(WINDOW_LENGTH, input_rows, input_cols, 1), data_format='channels_first'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Conv2D(input_rows, kernel_size=(3, 3), activation='relu', data_format='channels_first'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Conv2D(input_rows, kernel_size=(3, 3), activation='relu', data_format='channels_first'))
        model.add(MaxPooling2D(pool_size=(2, 2)))

        model.add(Flatten())
        model.add(Dense(512, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(NUMBER_OF_POSSIBLE_ACTIONS, activation='linear'))
    else:
        raise Exception("Invalid convolution layer dimension count")
    model.summary()

    # there isn't much documentation on parameters in following methods/classes...

    print("[INFO] Building DQNAgent...")
    basic_memory = SequentialMemory(limit=(10**6), window_length=WINDOW_LENGTH)

    # nb_steps should be related to TOTAL_NUMBER_OF_STEPS
    # nb_steps is the number of steps after which eps reaches value_min
    classic_policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05,
                                          nb_steps=1250000)

    bugfix_processor = DimensionKillerProcessor()   # THIS IS NECESSARY !

    dqn = DQNAgent(model=model, nb_actions=NUMBER_OF_POSSIBLE_ACTIONS, policy=classic_policy, memory=basic_memory, processor=bugfix_processor,
                   enable_double_dqn=False, enable_dueling_network=False, nb_steps_warmup=50000, gamma=.99,
                   target_model_update=10000, train_interval=4, delta_clip=1.)

    dqn.compile(Adam(lr=.00025), metrics=['mae'])

    # to check nvidia usage:
    # cmd
    # cd "C:\Program Files\NVIDIA Corporation\NVSMI"
    # .\nvidia-smi.exe
    # on GTX1080    step time: 27-40s 3-4ms/step - slows down with time    - Conv1D  input 64x64
    # on GTX1080    step time: 36-57s 3-6ms/step - slows down with time    - Conv2D  input 64x64
    # on GTX1080    step time: 25-33s 3-4ms/step - slows down with time    - Conv2D  input 32x32    not reached full RAM
    # sth is taking WAY too much memory - it keeps near 32GB used - 28GB for Python alone - but pagefile is not increasing
    # RAM usage drops -> step dime decreases
    # and after program is finished it takes > 30 min to free the memory... Better run from separate console window and after done terminate it

    print("[INFO] Training...")
    training_history = dqn.fit(env, nb_steps=TOTAL_NUMBER_OF_STEPS, verbose=VERBOSITY_LEVEL,
                               nb_max_episode_steps=20000, log_interval=VERBOSITY_1_LOGGER_INTERVAL)
    # episode_reward: average [min, max]

    print('-'*50)
    print("[INFO] Done training...")
    print("Played total of ", env.games_counter, " games")
    print("Won total of ", env.victory_counter, " games")
    env.print_map_victory_stats()
    print('-'*50)

    print(training_history.history.keys())
    print('-'*50)

    # save weights to file
    print("Saving dqn weights and stats")
    save_agent_weights_and_summary_to_file(base_file_name=BASE_WEIGHTS_FILE_NAME, number_of_steps_run=TOTAL_NUMBER_OF_STEPS,
                                           agent_to_save=dqn, used_model=model)
    print("Done saving dqn weights")
    env.save_game_stats_to_file(base_name=str(BASE_WEIGHTS_FILE_NAME + "_" + str(TOTAL_NUMBER_OF_STEPS)))
    print("Done saving stats")

    end_time = time.time()

    show_reward_plot(training_history, plot_title="BasicDQN")

    execution_time = end_time - start_time
    print(" >>>>>> ALL DONE. It took " + str(execution_time) + " seconds = " + str(execution_time / 60.0) + " minutes = " + str((execution_time / 60.0) / 60.0) + " hours")
    sys.exit(0)     # to free process memory immediately
