import sys
import time
import numpy as np
from keras.models import Sequential
from keras.layers import Flatten, Conv2D, Dense, MaxPooling2D, Dropout, Activation, MaxoutDense
from keras.optimizers import Adam, Nadam, SGD, RMSprop
from rl.agents.dqn import DQNAgent
from rl.policy import EpsGreedyQPolicy, LinearAnnealedPolicy, BoltzmannQPolicy
from rl.memory import SequentialMemory
from rl.callbacks import TrainEpisodeLogger, ModelIntervalCheckpoint
from SokobanEnv import SokobanEnv
from SokobanGame import SokobanGame
from DQNAgentUtils import DimensionKillerProcessor
from DQNAgentUtils import save_agent_weights_and_summary_to_file, show_reward_plot, load_agent_weights


# https://medium.com/emergent-future/simple-reinforcement-learning-with-tensorflow-part-7-action-selection-strategies-for-exploration-d3a97b7cceaf
# https://ml-cheatsheet.readthedocs.io/en/latest/index.html

BASE_WEIGHTS_FILE_NAME = "dqn_v1"

NUMBER_OF_POSSIBLE_ACTIONS = 4
MEMORY_LIMIT = 1 * (10 ** 6)
TOTAL_NUMBER_OF_STEPS = 6 * (10 ** 6)               # basic minimum is said to be 10 000 000                                                    <<<
NUMBER_OF_STEPS_FOR_EXPLORATION = 1 * (10 ** 6)
WINDOW_LENGTH = 1   # we dont need to have sense of directional heading and speed in Sokoban so WINDOW_LENGTH = 1 would be a natural choice
VERBOSITY_LEVEL = 1
AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS = 500

ENV_SIZE_ROWS = 32
ENV_SIZE_COLS = 32

VERBOSITY_1_LOGGER_INTERVAL = 10000

NUMBER_OF_INNER_CONVOLUTIONS = 2    # default 2                                                                                                 <<<
HIDDEN_ACTIVATION = 'relu'      # default 'selu'                                                                                                <<<
CONV_LAYER_SIZE_BASE = int(ENV_SIZE_ROWS)      # default int(ENV_SIZE_ROWS)
FIRST_CONV_KERNEL_SIZE = (4, 4)     # default (4, 4)                                                                                            <<<

DO_SCALE_ENV = False        # default False
DO_SCALE_REWARDS = False    # default False
EPISODE_LENGTH_OFFSET_IN_ENV_INIT = 0     # default 0
MAX_EPISODE_STEPS_IN_FIT_METHOD = 20000     # default 20000

GAMMA = 0.99       # default 0.99
MEMORY_REPLAY_BATCH_SIZE = 96   # default 32

DO_LOAD_WIEGHTS = False
WEIGHTS_FILE_NAME = 'test_weights.h5f'


def make_custom_model():
    custom_model = Sequential()
    # channels are always first
    custom_model.add(Conv2D(int(CONV_LAYER_SIZE_BASE / 2), kernel_size=FIRST_CONV_KERNEL_SIZE, input_shape=(WINDOW_LENGTH, input_rows, input_cols), data_format='channels_first'))
    custom_model.add(Activation(HIDDEN_ACTIVATION))
    # model.add(MaxPooling2D(pool_size=(2, 2)))

    for i in range(NUMBER_OF_INNER_CONVOLUTIONS):
        custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(3, 3), data_format='channels_first'))
        custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(3, 3)))
        custom_model.add(Activation(HIDDEN_ACTIVATION))
        # model.add(MaxPooling2D(pool_size=(2, 2)))

    custom_model.add(Flatten())
    custom_model.add(Dense(512))
    custom_model.add(Activation(HIDDEN_ACTIVATION))
    # custom_model.add(Dropout(0.2))
    #custom_model.add(Dense(NUMBER_OF_POSSIBLE_ACTIONS))
    custom_model.add(MaxoutDense(NUMBER_OF_POSSIBLE_ACTIONS, nb_feature=4))                                                                    # <<<
    custom_model.add(Activation('linear'))
    #custom_model.add(Activation('softmax'))

    return custom_model


if __name__ == "__main__":
    start_time = time.time()

    # first determine if we need bugfix processor and channel_first
    need_more_than_one_channel = False
    bugfix_processor = DimensionKillerProcessor()  # THIS IS NECESSARY WHEN WINDOW_LENGTH = 1 !
    if WINDOW_LENGTH != 1:  # if there is window length than we dont need bugfix processor as the principle is a bit different
        print(" WINDOW_LENGTH != 1 - WILL USE CHANNELS_FIRST")
        need_more_than_one_channel = True
        bugfix_processor = None

    SokobanEnv.configure_env_size(new_rows=ENV_SIZE_ROWS, new_cols=ENV_SIZE_COLS)
    #SokobanEnv.configure_difficulty_games_count_requirement(simple_threshold=1000,
    #                                                        medium_threshold=3000,
    #                                                        hard_threshold=15000,
    #                                                        very_hard_threshold=30000)
    env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT + EPISODE_LENGTH_OFFSET_IN_ENV_INIT,
                     put_map_in_the_center=True,
                     info_game_count=AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS,
                     use_bugged_dict_entries=False,
                     save_file_name='test_DQN_game_',
                     save_every_game_to_file=False,
                     map_choice_option=SokobanEnv.USE_MAPS_DIFFICULTY_LEVEL,
                     use_more_than_one_channel=need_more_than_one_channel,
                     scale_rewards=DO_SCALE_REWARDS,
                     scale_range=(-1, 1),
                     use_scaled_env_representation=DO_SCALE_ENV,
                     disable_map_rotation=False)

    print("[INFO] Building model...")
    print("Environment size is: rows: " + str(env.GAME_SIZE_ROWS) + " cols: " + str(env.GAME_SIZE_COLS))
    print("Memory window length is: " + str(WINDOW_LENGTH))
    input_rows = SokobanEnv.GAME_SIZE_ROWS
    input_cols = SokobanEnv.GAME_SIZE_COLS
    model = make_custom_model()
    model.summary()

    print("[INFO] Building DQNAgent...")
    basic_memory = SequentialMemory(limit=MEMORY_LIMIT, window_length=WINDOW_LENGTH)

    #action_choice_policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05, nb_steps=NUMBER_OF_STEPS_FOR_EXPLORATION)
    action_choice_policy = BoltzmannQPolicy(tau=1., clip=(-500., 500.))

    dqn = DQNAgent(model=model, nb_actions=NUMBER_OF_POSSIBLE_ACTIONS, policy=action_choice_policy, memory=basic_memory,
                   processor=bugfix_processor, batch_size=MEMORY_REPLAY_BATCH_SIZE,
                   enable_double_dqn=True, enable_dueling_network=True, nb_steps_warmup=50000, gamma=GAMMA,
                   target_model_update=10000, train_interval=4, delta_clip=1.)

    opt = Adam(lr=.00025)       # default
    #opt = Nadam(lr=.0005)
    #opt = SGD(lr=0.00025, momentum=0.9, nesterov=True)
    dqn.compile(optimizer=opt, metrics=['mae'])

    if DO_LOAD_WIEGHTS:
        print("[INFO] Loading weights from file: " + WEIGHTS_FILE_NAME)
        load_agent_weights(dqn, WEIGHTS_FILE_NAME)

    print("[INFO] Training...")
    training_history = dqn.fit(env, nb_steps=TOTAL_NUMBER_OF_STEPS, verbose=VERBOSITY_LEVEL,
                               nb_max_episode_steps=MAX_EPISODE_STEPS_IN_FIT_METHOD, log_interval=VERBOSITY_1_LOGGER_INTERVAL)

    print('-' * 50)
    print("[INFO] Done training...")
    print("Played total of ", env.games_counter, " games")
    print("Won total of ", env.victory_counter, " games")
    env.print_map_victory_stats()
    print('-' * 50)

    # save weights to file
    print("Saving dqn weights and stats")
    save_agent_weights_and_summary_to_file(base_file_name=BASE_WEIGHTS_FILE_NAME,
                                           number_of_steps_run=TOTAL_NUMBER_OF_STEPS,
                                           agent_to_save=dqn, used_model=model)
    print("Done saving dqn weights")
    env.save_game_stats_to_file(base_name=str(BASE_WEIGHTS_FILE_NAME + "_" + str(TOTAL_NUMBER_OF_STEPS)))
    print("Done saving stats")

    end_time = time.time()

    show_reward_plot(training_history, plot_title="DQN_v1")

    execution_time = end_time - start_time
    print(" >>>>>> ALL DONE. It took " + str(execution_time) + " seconds = " + str(execution_time / 60.0) + " minutes = " + str((execution_time / 60.0) / 60.0) + " hours")
    sys.exit(0)  # to free process memory immediately
