import sys
import time
import argparse
import numpy as np
from keras.models import Sequential
from keras.layers import Flatten, Conv2D, Dense, Activation, MaxoutDense, LeakyReLU, PReLU, MaxPooling2D
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from rl.agents.dqn import DQNAgent
from rl.callbacks import ModelIntervalCheckpoint
from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory
from SokobanEnv import SokobanEnv
from SokobanGame import SokobanGame
from MemoryLoader import SokobanManualGameMemoryLoader
from DQNAgentUtils import DimensionKillerProcessor
from DQNAgentUtils import save_agent_weights_and_summary_to_file, show_reward_plot, load_agent_weights, \
    PATH_TO_SAVED_MODELS, load_optimizer_from_file


# to use BatchNormalization with channels_first this commit is needed to be added manually:
# https://github.com/keras-team/keras/commit/e3a2f7d29f2f1c21ecc978bd0038b1d1330d33c2


NO_TEST = '__no_test__'
NO_OPTIMIZER = '__no_optimizer__'
NO_STEPS_SPECIFIED = -1

NUMBER_OF_POSSIBLE_ACTIONS = 4
MEMORY_LIMIT = 1 * (10 ** 6)
TOTAL_NUMBER_OF_STEPS = 6 * (10 ** 6)
NUMBER_OF_STEPS_FOR_EXPLORATION = 1 * (10 ** 6)
DEFAULT_CALLBACK_INTERVAL = 1 * (10 ** 6)
WINDOW_LENGTH = 1
VERBOSITY_LEVEL = 1
AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS = 500

ENV_SIZE_ROWS = 32
ENV_SIZE_COLS = 32

VERBOSITY_1_LOGGER_INTERVAL = 10000

NUMBER_OF_INNER_CONVOLUTIONS = 4
HIDDEN_ACTIVATION = 'prelu'
CONV_LAYER_SIZE_BASE = int(ENV_SIZE_ROWS)
FIRST_CONV_KERNEL_SIZE = (4, 4)

GAMMA = 0.99
MEMORY_REPLAY_BATCH_SIZE = 96

DO_LOAD_GAMES_FROM_FILES = False
LOADED_GAMES_MEMORY_LIMIT = MEMORY_LIMIT

NUMBER_OF_STEPS_FOR_WARMUP = 50000

NUMBER_OF_EPISODES_FOR_TESTING = 1000

SAVE_EVERY_GAME = False


def get_hidden_layer_activation(option):
    """ To allow keras advanced activations like LeakyReLU or PReLU """
    if option == 'leakyrelu':
        return LeakyReLU()
    elif option == 'prelu':
        return PReLU()
    else:
        return Activation(option)


def make_custom_model(input_rows, input_cols):
    custom_model = Sequential()
    # channels are always first
    custom_model.add(Conv2D(int(CONV_LAYER_SIZE_BASE / 2), kernel_size=FIRST_CONV_KERNEL_SIZE, input_shape=(WINDOW_LENGTH, input_rows, input_cols), data_format='channels_first'))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    for i in range(NUMBER_OF_INNER_CONVOLUTIONS):
        custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(3, 3), data_format='channels_first'))
        custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Flatten())
    custom_model.add(Dense(512))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(MaxoutDense(NUMBER_OF_POSSIBLE_ACTIONS, nb_feature=4))
    custom_model.add(Activation('linear'))
    return custom_model


def make_custom_model_3_norm(input_rows, input_cols):
    """ roughly based on VGG and this: https://www.scitepress.org/papers/2018/67520/67520.pdf
        It would probably be better to save model of this network more often with -ci parameter set to 100k or even less
    """
    try:
        if not args.scale_env:
            raise ValueError('This network requires Scaled Env! Use -sc option!')
    except NameError:
        pass

    global HIDDEN_ACTIVATION

    custom_model = Sequential()
    custom_model.add(Conv2D(64, kernel_size=(3, 3), input_shape=(WINDOW_LENGTH, input_rows, input_cols),
                            data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))  # axis=1 due to Conv2D with channels_first
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(64, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Conv2D(128, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(128, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Conv2D(256, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(256, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(256, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Conv2D(512, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(512, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(512, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Conv2D(512, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(512, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))

    custom_model.add(Flatten())
    custom_model.add(Dense(384))
    custom_model.add(BatchNormalization())
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(MaxoutDense(NUMBER_OF_POSSIBLE_ACTIONS, nb_feature=4))
    custom_model.add(Activation('linear'))
    return custom_model


def make_custom_model_2(input_rows, input_cols):
    global HIDDEN_ACTIVATION

    custom_model = Sequential()
    custom_model.add(Conv2D(int(CONV_LAYER_SIZE_BASE / 2), kernel_size=(7, 7), strides=2,
                            input_shape=(WINDOW_LENGTH, input_rows, input_cols), data_format='channels_first'))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(5, 5), data_format='channels_first'))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Flatten())
    custom_model.add(Dense(512))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(MaxoutDense(NUMBER_OF_POSSIBLE_ACTIONS, nb_feature=4))
    custom_model.add(Activation('linear'))
    return custom_model


def make_custom_model_2_norm(input_rows, input_cols):
    global HIDDEN_ACTIVATION

    custom_model = Sequential()
    custom_model.add(Conv2D(int(CONV_LAYER_SIZE_BASE / 2), kernel_size=(7, 7), strides=2,
                            input_shape=(WINDOW_LENGTH, input_rows, input_cols), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))    # axis=1 due to Conv2D with channels_first
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(5, 5), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Conv2D(CONV_LAYER_SIZE_BASE, kernel_size=(3, 3), data_format='channels_first'))
    custom_model.add(BatchNormalization(axis=1))
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(Flatten())
    custom_model.add(Dense(512))
    #custom_model.add(BatchNormalization())
    custom_model.add(get_hidden_layer_activation(HIDDEN_ACTIVATION))
    custom_model.add(MaxoutDense(NUMBER_OF_POSSIBLE_ACTIONS, nb_feature=4))
    custom_model.add(Activation('linear'))
    return custom_model


def get_new_sokoban_env(for_test: bool, is_first_training: bool, use_generated_maps: bool, use_scaled_env: bool = False):
    SokobanEnv.configure_env_size(new_rows=ENV_SIZE_ROWS, new_cols=ENV_SIZE_COLS)
    if use_generated_maps:
        map_choice_option = SokobanEnv.USE_GENERATED_MAPS
    elif not for_test:
        map_choice_option = SokobanEnv.USE_MAPS_DIFFICULTY_LEVEL
    else:
        map_choice_option = SokobanEnv.USE_MAPS_FROM_FILE
    if not for_test and is_first_training:
        SokobanEnv.configure_difficulty_games_count_requirement(100, 1000, 2500, 5000)  # to get more maps quicker
        agent_env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT,
                               put_map_in_the_center=True,
                               info_game_count=AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS,
                               use_bugged_dict_entries=False,
                               save_file_name='final_DQN_game_',
                               save_every_game_to_file=SAVE_EVERY_GAME,
                               map_choice_option=map_choice_option,
                               use_more_than_one_channel=False,
                               scale_rewards=False,
                               scale_range=(-1, 1),
                               use_scaled_env_representation=use_scaled_env,
                               disable_map_rotation=False)
        return agent_env
    elif not for_test and not is_first_training:
        SokobanEnv.configure_difficulty_games_count_requirement(0, 0, 0, 0)     # to use all non test maps
        agent_env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT,
                               put_map_in_the_center=True,
                               info_game_count=AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS,
                               use_bugged_dict_entries=False,
                               save_file_name='final_DQN_game_',
                               save_every_game_to_file=SAVE_EVERY_GAME,
                               map_choice_option=map_choice_option,
                               use_more_than_one_channel=False,
                               scale_rewards=False,
                               scale_range=(-1, 1),
                               use_scaled_env_representation=use_scaled_env,
                               disable_map_rotation=False)
        return agent_env
    else:   # for testing
        agent_env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT,
                               put_map_in_the_center=True,
                               info_game_count=AFTER_HOW_MANY_GAMES_PRINT_VICTORY_STATS,
                               use_bugged_dict_entries=False,
                               save_file_name='final_DQN_game_TEST_',
                               save_every_game_to_file=True,        # save every game
                               map_choice_option=map_choice_option,
                               use_more_than_one_channel=False,
                               scale_rewards=False,
                               scale_range=(-1, 1),
                               use_scaled_env_representation=use_scaled_env,
                               disable_map_rotation=False)
        return agent_env


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-t", "--test", type=str,
                             help="file name of weights file to load, by default uses maps specified in file (see SokobanEnv)",
                             dest="test_weights", default=NO_TEST)
    args_parser.add_argument("-c", "--continue", type=str,
                             help="file name of weights file to load, used to continue training",
                             dest="training_weights", default=NO_TEST)
    args_parser.add_argument("-n", "--n_steps", type=int,
                             help="number of steps if training or number of episodes if testing",
                             dest="n_steps", default=NO_STEPS_SPECIFIED)
    args_parser.add_argument("-f", "--first_training", help="indicates that it is a first training for the network",
                             action="store_true", dest="is_first_traning")
    args_parser.add_argument("-s", "--save_always", help="if set every game will be saved, default True if --test",
                             action="store_true", dest="save_always")
    args_parser.add_argument("-l", "--load_manual", help="if set manual games will be loaded to agents memory",
                             action="store_true", dest="load_manual")
    args_parser.add_argument("-g", "--generated_maps", help="if set agent will train/test on generated maps. " +
                                                            "Stats saving is disabled due to not having static map names",
                             action="store_true", dest="generated_maps")
    args_parser.add_argument("-sc", "--scale_env", help="if set will use scaled env representation",
                             action="store_true", dest="scale_env")
    args_parser.add_argument("-ci", "--callback_interval", type=int,
                             help="number of steps after which callbacks will be called during training",
                             dest="callback_interval", default=DEFAULT_CALLBACK_INTERVAL)
    args_parser.add_argument("-m", "--model_type", type=str,
                             help="type of loaded model 1 - default, 2 diffconv, 2n diffconv with batch normalization, 3n - final network",
                             choices=['1', '2', '2n', '3n'],
                             dest="model_type", default='3n')
    args_parser.add_argument("-o", "--optimizer", type=str,
                             help="file name of file with optimizer object to load",
                             dest="optimizer", default=NO_OPTIMIZER)
    args_parser.add_argument("--relu", help="if set will use relu activation function", action="store_true", dest="use_relu")
    args = args_parser.parse_args()
    if args.test_weights != NO_TEST:
        weights_file_name = args.test_weights
        is_test = True
    else:
        weights_file_name = ""
        is_test = False
    if args.n_steps == NO_STEPS_SPECIFIED:
        number_of_steps = TOTAL_NUMBER_OF_STEPS
        number_of_episodes = NUMBER_OF_EPISODES_FOR_TESTING
    elif args.n_steps > 0:
        number_of_steps = args.n_steps
        number_of_episodes = args.n_steps
    else:
        raise ValueError('Invalid n_steps number')
    if args.save_always:
        print("[INFO] Saving EVERY games played by the agent")
        SAVE_EVERY_GAME = True
    if args.load_manual:
        DO_LOAD_GAMES_FROM_FILES = True
    if args.generated_maps:
        use_generated_maps = True
    else:
        use_generated_maps = False
    if args.use_relu:
        HIDDEN_ACTIVATION = 'relu'

    start_time = time.time()

    bugfix_processor = DimensionKillerProcessor()

    env = get_new_sokoban_env(for_test=is_test, is_first_training=args.is_first_traning,
                              use_generated_maps=use_generated_maps, use_scaled_env=args.scale_env)

    print("[INFO] Building model...")
    if args.model_type == '1':
        model = make_custom_model(input_cols=ENV_SIZE_COLS, input_rows=ENV_SIZE_ROWS)
    elif args.model_type == '2':
        model = make_custom_model_2(input_cols=ENV_SIZE_COLS, input_rows=ENV_SIZE_ROWS)
    elif args.model_type == '2n':
        model = make_custom_model_2_norm(input_cols=ENV_SIZE_COLS, input_rows=ENV_SIZE_ROWS)
    elif args.model_type == '3n':
        model = make_custom_model_3_norm(input_cols=ENV_SIZE_COLS, input_rows=ENV_SIZE_ROWS)
    else:
        raise ValueError('Unknown model type!')
    model.summary()

    if DO_LOAD_GAMES_FROM_FILES and not is_test:
        NUMBER_OF_STEPS_FOR_WARMUP = 0      # don't do warmup moves - we already have filled memory

    print("[INFO] Building DQNAgent...")
    basic_memory = SequentialMemory(limit=MEMORY_LIMIT, window_length=WINDOW_LENGTH)
    action_choice_policy = BoltzmannQPolicy(tau=1., clip=(-500., 500.))
    #action_choice_policy = EpsGreedyQPolicy(eps=0.1)

    # maybe train_interval=1 ?
    dqn = DQNAgent(model=model, nb_actions=NUMBER_OF_POSSIBLE_ACTIONS, policy=action_choice_policy, memory=basic_memory,
                   processor=bugfix_processor, batch_size=MEMORY_REPLAY_BATCH_SIZE, test_policy=action_choice_policy,
                   enable_double_dqn=True, enable_dueling_network=True, nb_steps_warmup=NUMBER_OF_STEPS_FOR_WARMUP,
                   gamma=GAMMA, target_model_update=10000, train_interval=4, delta_clip=1.)
    if args.optimizer != NO_OPTIMIZER:
        print('Loading optimizer from ' + args.optimizer)
        opt = load_optimizer_from_file(args.optimizer)
    else:
        print('Using new optimizer object')
        if args.model_type == '3n':
            opt = Adam(lr=.00025, clipnorm=1.0)  # clipnorm so that there are no exploding gradients
        else:
            opt = Adam(lr=.00025)
    dqn.compile(optimizer=opt, metrics=['mae'])

    if is_test:
        print("[INFO] Loading weights from file: " + weights_file_name)
        load_agent_weights(dqn, weights_file_name)
        print("[INFO] Done loading")
        do_train = False
    elif not args.is_first_traning:
        file_name = args.training_weights
        print("[INFO] Loading weights from file: " + file_name)
        load_agent_weights(dqn, file_name)
        print("[INFO] Done loading")
        do_train = True
    else:
        print("[INFO] beginning first training")
        do_train = True

    if DO_LOAD_GAMES_FROM_FILES and do_train:
        print("[INFO] Loading recorded games. This may take a while...")
        game_record_loader = SokobanManualGameMemoryLoader(agent_memory=basic_memory,
                                                           memory_limit=LOADED_GAMES_MEMORY_LIMIT)
        game_record_loader.load_all_games()

    if do_train:
        # save model weights after N steps
        checkpoint_weights_filename = PATH_TO_SAVED_MODELS + '_checkpoint_dqn_weights_{step}.h5f'
        callbacks = [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=args.callback_interval)]

        print("[INFO] Training...")
        training_history = dqn.fit(env, nb_steps=number_of_steps, verbose=VERBOSITY_LEVEL, nb_max_episode_steps=10000,
                                   log_interval=VERBOSITY_1_LOGGER_INTERVAL, callbacks=callbacks)
        # save weights to file
        print("Saving dqn weights and stats")
        save_agent_weights_and_summary_to_file(base_file_name="final_DQN_",
                                               number_of_steps_run=TOTAL_NUMBER_OF_STEPS,
                                               agent_to_save=dqn, used_model=model, used_optimizer=opt)
        print("Done saving dqn weights")
    else:   # test
        print("[INFO] Testing on maps specified in file " + SokobanEnv.SPECIFIC_MAPS_FILE_NAME)
        dqn.test(env, nb_episodes=number_of_episodes, visualize=False)

    print('-' * 50)
    print("[INFO] Done...")
    print("Played total of ", env.games_counter, " games")
    print("Won total of ", env.victory_counter, " games")
    if not use_generated_maps:  # don't print/save stats if using generated maps due to the every generated map having unique name
        env.print_map_victory_stats()
    print('-' * 50)

    if not use_generated_maps:  # don't print/save stats if using generated maps due to the every generated map having unique name
        env.save_game_stats_to_file(base_name=str("final_DQN_" + str(TOTAL_NUMBER_OF_STEPS)))
    print("Done saving stats")

    end_time = time.time()

    if do_train:
        show_reward_plot(training_history, plot_title="DQN_v1")

    execution_time = end_time - start_time
    print(" >>>>>> ALL DONE. It took " + str(execution_time) + " seconds = " + str(execution_time / 60.0) + " minutes = " + str((execution_time / 60.0) / 60.0) + " hours")
    sys.exit(0)  # to free process memory immediately
