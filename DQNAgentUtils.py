import os
import joblib
import datetime
import numpy as np
import matplotlib.pyplot as plt
from rl.core import Processor

# Functions and classes common for DQN agents

PATH_TO_SAVED_MODELS = "trained_models/"
OPTIMIZER_EXTENSION = '.joblib'

# to check nvidia usage:
# cmd
# cd "C:\Program Files\NVIDIA Corporation\NVSMI"
# .\nvidia-smi.exe


class DimensionKillerProcessor(Processor):
    """ acts as a coupling mechanism between the agent and the environment """

    def process_state_batch(self, batch):
        """
        Given a state batch, I want to remove the second dimension, because it's
        useless and prevents me from feeding the tensor into my CNN

        This processor removes one dimension from state_batch that is added there by some bug in keras-rl
        Without this keras would raise an error that it has too many dimensions in first Conv layer \n
        This only applies if input has only one channel!

        Based on: \n
        # https://github.com/keras-rl/keras-rl/issues/306   \n
        # https://github.com/keras-rl/keras-rl/issues/238   \n
        # https://github.com/keras-rl/keras-rl/issues/229#issuecomment-482913659
        """
        return np.squeeze(batch, axis=1)


def save_agent_weights_and_summary_to_file(base_file_name: str, number_of_steps_run: int, agent_to_save, used_model, used_optimizer=None):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename_base = PATH_TO_SAVED_MODELS + base_file_name + "_" + str(number_of_steps_run) + "_steps_" + current_date
    model_desc_filename = filename_base + "_model_summary.txt"
    weights_filename = filename_base + "_weights.h5f"

    # write model summary to file
    with open(model_desc_filename, 'w+') as fh:
        # Pass the file handle in as a lambda function to make it callable
        used_model.summary(print_fn=lambda x: fh.write(x + '\n'))

    agent_to_save.save_weights(weights_filename)

    if used_optimizer is not None:
        optimizer_file_path = PATH_TO_SAVED_MODELS + base_file_name + "_optimizer_" + type(used_optimizer).__name__ + \
                              "_steps_" + current_date + OPTIMIZER_EXTENSION
        joblib.dump(used_optimizer, optimizer_file_path)


def load_agent_weights(agent_obj, weights_file_path):
    if os.path.isfile(weights_file_path):
        agent_obj.load_weights(weights_file_path)
        return agent_obj
    else:
        msg = "ERROR! Weights file not found at given location: " + weights_file_path
        print(msg)
        raise ValueError(msg)


def load_optimizer_from_file(file_path):
    loaded_optimizer = joblib.load(file_path)
    return loaded_optimizer


def show_reward_plot(training_history, plot_title: str, plot_nb_episode_steps: bool = False):
    plt.plot(training_history.history['episode_reward'])
    legend_entries = ['episode_reward']
    if plot_nb_episode_steps:
        y_label = 'Reward/steps for 1 episode'
        plt.plot(training_history.history['nb_episode_steps'])
        legend_entries.append('nb_episode_steps')
    else:
        y_label = 'Reward for 1 episode'
    plt.axhline(y=0.0, color='r', linestyle='--', linewidth=2.0)
    plt.title(plot_title)
    plt.ylabel(y_label)
    plt.xlabel('Episodes (games played)')
    plt.legend(legend_entries, loc='lower right')
    plt.show()
