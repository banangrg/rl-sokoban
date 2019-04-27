import datetime
import numpy as np
from keras.models import Sequential
from keras.layers import Flatten, Conv2D, Dense, MaxPooling2D, Dropout, Conv1D, MaxPooling1D
from keras.optimizers import Adam
from rl.agents.dqn import DQNAgent
from rl.policy import EpsGreedyQPolicy, LinearAnnealedPolicy
from rl.memory import SequentialMemory
from rl.core import Processor
from rl.callbacks import TrainEpisodeLogger, ModelIntervalCheckpoint
from SokobanEnv import SokobanEnv
from SokobanGame import SokobanGame
import matplotlib.pyplot as plt


# TODO: IMPORTANT!!! Sometomes there is some KeyError inside keras-rl. Use this as workaround
# add try-except KeyError in C:\Users\user\AppData\Local\Programs\Python\Python36\Lib\site-packages\rl\callbacks.py
# around 279 line
#try:
#    if len(self.info_names) > 0:
#        self.infos.append([logs['info'][k] for k in self.info_names])
#except KeyError:
#    print("Caught error in logging - trying to continue")


PATH_TO_SAVED_MODELS = "trained_models/"
BASE_WEIGHTS_FILE_NAME = "test_basic_dqn_"

NUMBER_OF_POSSIBLE_ACTIONS = 4
TOTAL_NUMBER_OF_STEPS = 1000000   # basic minimum is said to be 10 000 000
WINDOW_LENGTH = 1   # we dont need to have sense of directional heading and speed
VERBOSITY_LEVEL = 1
AFTER_HOW_MANY_GAMES_PRINT_STATS = 500

CONV_LAYER_DIMENSION = 2


class DimensionKillerProcessor(Processor):
    """ acts as a coupling mechanism between the agent and the environment """

    def process_state_batch(self, batch):
        """
        Given a state batch, I want to remove the second dimension, because it's
        useless and prevents me from feeding the tensor into my CNN

        This processor removes one dimension from state_batch that is added there by some bug in keras-rl
        Without this keras would raise an error that it has too many dimensions in first Conv layer

        Based on: \n
        # https://github.com/keras-rl/keras-rl/issues/306   \n
        # https://github.com/keras-rl/keras-rl/issues/238   \n
        # https://github.com/keras-rl/keras-rl/issues/229#issuecomment-482913659
        """
        return np.squeeze(batch, axis=1)


env = SokobanEnv(game_timeout=SokobanGame.DEFAULT_TIMEOUT,
                 put_map_in_the_center=True,
                 info_game_count=AFTER_HOW_MANY_GAMES_PRINT_STATS)

print("A basic DQN Agent to test if SokobanEnv is working")

print("[INFO] Building model...")
# maybe MaxPoolingND and Dropout not necessary?
if CONV_LAYER_DIMENSION == 1:
    model = Sequential()
    model.add(Conv1D(32, kernel_size=4, activation='relu', input_shape=(SokobanEnv.GAME_SIZE_ROWS, SokobanEnv.GAME_SIZE_COLS)))
    model.add(MaxPooling1D(pool_size=2))

    model.add(Conv1D(64, kernel_size=3, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))

    model.add(Conv1D(64, kernel_size=3, activation='relu'))
    model.add(MaxPooling1D(pool_size=2))

    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(NUMBER_OF_POSSIBLE_ACTIONS, activation='linear'))
elif CONV_LAYER_DIMENSION == 2:
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(4, 4), activation='relu',input_shape=(SokobanEnv.GAME_SIZE_ROWS, SokobanEnv.GAME_SIZE_COLS, 1)))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))

    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(NUMBER_OF_POSSIBLE_ACTIONS, activation='linear'))
else:
    raise Exception("Invalid convolution layer dimension count")

model.summary()

print("[INFO] Building DQNAgent...")
basic_memory = SequentialMemory(limit=1000000, window_length=WINDOW_LENGTH)

# nb_steps_should be related to TOTAL_NUMBER_OF_STEPS
classic_policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05,
                                      nb_steps=1250000)

bugfix_processor = DimensionKillerProcessor()

# there isn't much documentation on these parameters
dqn = DQNAgent(model=model, nb_actions=NUMBER_OF_POSSIBLE_ACTIONS, policy=classic_policy, memory=basic_memory, processor=bugfix_processor,
               enable_double_dqn=False, enable_dueling_network=False, nb_steps_warmup=50000, gamma=.99,
               target_model_update=10000, train_interval=4, delta_clip=1.)

dqn.compile(Adam(lr=.00025), metrics=['mae'])

# to check nvidia usage:
# cmd
# cd "C:\Program Files\NVIDIA Corporation\NVSMI"
# .\nvidia-smi.exe
# on GTX1080    step time: 27-40s 3ms/step - slows down with time           - Conv1D
# on GTX1080    step time: 36-48s 3ms/step - slows down with time           - Conv2D
# sth is taking WAY too much memory - it keeps near 32GB used - 28GB for Python alone - but pagefile is not increasing
# and after program is finished it takes > 30 min to free the memory...

print("[INFO] Training...")
training_history = dqn.fit(env, nb_steps=TOTAL_NUMBER_OF_STEPS, verbose=VERBOSITY_LEVEL, nb_max_episode_steps=20000, log_interval=10000)

print('-'*50)
print("Played total of ", env.games_counter, " games")
print("Won total of ", env.victory_counter, " games")
print('-'*50)

print(training_history.history.keys())
print('-'*50)

# save weights to file
print("Saving dqn weights")
current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
filename = PATH_TO_SAVED_MODELS + BASE_WEIGHTS_FILE_NAME + str(TOTAL_NUMBER_OF_STEPS) + "_steps_" + current_date + ".h5f"
dqn.save_weights(filename)
print("Done saving dqn weights")

plt.plot(training_history.history['episode_reward'])
plt.plot(training_history.history['nb_episode_steps'])
plt.title('Rewards and steps')
plt.ylabel('Rewards and steps for 1 episode')
plt.xlabel('Episodes (games)')
plt.legend(['episode_reward', 'nb_episode_steps'], loc='lower right')
plt.show()

print("ALL DONE")
