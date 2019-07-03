import os
import re
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from stat import S_ISREG, ST_CTIME, ST_MODE


STEPS_PER_ENTRY = 10000
EXCLUDED_FILE_PREFIX = '__'
CHART_TICK_INTERVAL = 1000
CHART_2_TICK_INTERVAL = 500
CHART_MAKER_FILES_DIR = "chart_maker_files/"
ENTRY_REGEX = "(\d+\/\d+\s+\[[=>.]*\]\s+.*\s.*-\slevel_rotation_option:\s\d+\.?\d+)"
EPISODE_REGEX = "(\d+)\sepisodes"
EPISODE_AVG_REWARD_REGEX = "episode_reward:\s(-?\d+(?:\.\d+))\s\[-?\d+(?:\.\d+),\s-?\d+(?:\.\d+)\]"
EPISODE_MIN_REWARD_REGEX = "episode_reward:\s-?\d+(?:\.\d+)\s\[(-?\d+(?:\.\d+)),\s-?\d+(?:\.\d+)\]"
EPISODE_MAX_REWARD_REGEX = "episode_reward:\s-?\d+(?:\.\d+)\s\[-?\d+(?:\.\d+),\s(-?\d+(?:\.\d+))\]"
REWARD_REGEX = "\sreward:\s(-?\d+(?:\.\d+))"
LOSS_REGEX = "loss:\s(\d+(?:\.\d+))"
MAE_REGEX = "mean_absolute_error:\s(\d+(?:\.\d+))"
Q_REGEX = "mean_q:\s(-?\d+(?:\.\d+))"
GAMES_WON_REGEX = "(\d+\/\d+)\sgames\swon\sin\sthis\slogging\speriod"
GAMES_WON_1_REGEX = "(\d+)\/"
GAMES_WON_2_REGEX = "\/(\d+)"
STEPS_PER_ENTRY_REGEX = "\d+\/(\d+)\s\[[=>.]*\]"


args_parser = argparse.ArgumentParser()
args_parser.add_argument("-f", "--file", type=str, help="path to directory with files to load",
                         dest="file_path", default=CHART_MAKER_FILES_DIR)
args_parser.add_argument("-fs", "--font_size", type=int, help="size of font", dest="font_size", default=16)
args_parser.add_argument("-ts", "--ticks_font_size", type=int, help="size of font of ticks", dest="ticks_font_size", default=14)
args_parser.add_argument("-y", '--values', nargs='+', type=int,
                         help="list separated with space of values to plot, use -yh to print available ones",
                         dest="values", default=[0, 1, 2])
args_parser.add_argument("-yh", "--values_help", help="if set prints available values", action="store_true",
                         dest="print_values_help")
args_parser.add_argument("-t1", "--tick_1_interval", type=int, help="interval of ticks on 1st chart", dest="ticks_interval_1", default=CHART_TICK_INTERVAL)
args_parser.add_argument("-t2", "--tick_2_interval", type=int, help="interval of ticks on 2nd chart", dest="ticks_interval_2", default=CHART_2_TICK_INTERVAL)
args_parser.add_argument("-s", "--steps", help="if set uses steps instead of episodes in x", action="store_true",
                         dest="use_steps")
args_parser.add_argument("-a", "--alphabetical", help="if set uses alphabetical sort of files instead of by modification time, "
                                                      "use this option if you will correctly name the files (ex. first one 'a.txt', second 'b.txt', etc.)",
                         action="store_true", dest="sort_alphabetical")
args = args_parser.parse_args()

used_files_dir = args.file_path
font_size = args.font_size
ticks_font_size = args.ticks_font_size
values_to_plot = args.values
ticks_1_interval = args.ticks_interval_1
ticks_2_interval = args.ticks_interval_2

# load files
files_to_load = [used_files_dir + file for file in os.listdir(used_files_dir) if not file.startswith(EXCLUDED_FILE_PREFIX)]
if args.sort_alphabetical:
    print('Sorting files alphabetically')
    files_to_load.sort()
else:
    print('Sorting files by modification time')
    files_to_load.sort(key=lambda x: os.path.getmtime(x))
print('Using files:', files_to_load)

entries = []
games_won_stats_entries = []
entry_pattern = re.compile(ENTRY_REGEX)
games_won_pattern = re.compile(GAMES_WON_REGEX)
# read files and process them
for file in files_to_load:
    with open(file, 'r') as f:
        read_data = f.read()

    # find entries and append them to list
    for match in re.finditer(entry_pattern, read_data):
        entries.append(match.group(1))

    for match in re.finditer(games_won_pattern, read_data):
        games_won_stats_entries.append(match.group(1))

# process entries and pack data into relevant lists
current_episodes_counter = 0
current_steps_counter = 0
episodes_counters = []
steps_counters = []
episodes_counters_not_full = []
steps_counters_not_full = []
episode_rewards_avg = []
episode_rewards_min = []
episode_rewards_max = []
rewards_avg = []
losses_avg = []
mae_avg = []
q_avg = []
for entry in entries:
    current_episodes_counter += int(re.findall(EPISODE_REGEX, entry)[0])
    current_steps_counter += int(re.findall(STEPS_PER_ENTRY_REGEX, entry)[0])
    episodes_counters.append(current_episodes_counter)
    steps_counters.append(current_steps_counter)
    episode_rewards_avg.append(float(re.findall(EPISODE_AVG_REWARD_REGEX, entry)[0]))
    episode_rewards_min.append(float(re.findall(EPISODE_MIN_REWARD_REGEX, entry)[0]))
    episode_rewards_max.append(float(re.findall(EPISODE_MAX_REWARD_REGEX, entry)[0]))
    if 'loss: ' in entry:
        episodes_counters_not_full.append(current_episodes_counter)
        steps_counters_not_full.append(current_steps_counter)
        rewards_avg.append(float(re.findall(REWARD_REGEX, entry)[0]))
        losses_avg.append(float(re.findall(LOSS_REGEX, entry)[0]))
        mae_avg.append(float(re.findall(MAE_REGEX, entry)[0]))
        q_avg.append(float(re.findall(Q_REGEX, entry)[0]))

games_won_in_period_list = []
games_all_in_period_list = []
games_played_counter = 0
for stats_entry in games_won_stats_entries:
    games_won_in_period_list.append(float(re.findall(GAMES_WON_1_REGEX, stats_entry)[0]))
    games_played_counter += int(re.findall(GAMES_WON_2_REGEX, stats_entry)[0])
    games_all_in_period_list.append(games_played_counter)

# finally make the chart
_color = 0
_value_list = 1
_name = 2
_uses_different_x = 3
_key = 0
_value = 1
all_lists_dict = {
    0: ['g-', episode_rewards_avg, 'average reward', False],
    1: ['b-', episode_rewards_min, 'min reward', False],
    2: ['r-', episode_rewards_max, 'max reward', False],
    3: ['y-', rewards_avg, 'average reward for step', True],
    4: ['c-', losses_avg, 'average loss', True],
    5: ['m-', mae_avg, 'average Mean Absolute Error', True],
    6: ['k-', q_avg, 'average Q value', True]
}

if args.print_values_help:
    print('Available values to plot:')
    for item in all_lists_dict.items():
        print(item[_key], '-', item[_value][_name])

lists_to_plot = [entry[_value] for entry in all_lists_dict.items() if entry[_key] in values_to_plot]

plt.style.use('seaborn')
legend_entries = []
for item in lists_to_plot:
    # determine the right x values list
    if args.use_steps:
        x_to_use = steps_counters
        ticks_range = np.arange(min(steps_counters), max(steps_counters) + 1, ticks_1_interval)
        if item[_uses_different_x]:
            x_to_use = steps_counters_not_full

        if ticks_1_interval == CHART_TICK_INTERVAL:
            ticks_1_interval = 50000
    else:
        x_to_use = episodes_counters
        ticks_range = np.arange(min(steps_counters), max(steps_counters) + 1, ticks_1_interval)
        if item[_uses_different_x]:
            x_to_use = episodes_counters_not_full

    # than add plot and legend entry
    plt.plot(x_to_use, item[_value_list], item[_color])
    legend_entries.append(item[_name])

plt.axhline(y=0.0, color='k', linestyle='--', linewidth=1.0)
plt.xticks(ticks_range)
plt.tick_params(axis='both', which='major', labelsize=ticks_font_size)
plt.title('FinalDQN rewards statistics plot', fontsize=font_size)
plt.ylabel('Reward', fontsize=font_size)
plt.xlabel('Episodes (games played)', fontsize=font_size)
plt.legend(legend_entries, loc='lower right', prop={'size': font_size})
plt.show()

plt.plot(games_all_in_period_list, games_won_in_period_list, 'b-')
legend_entries = ['games won in period of 500 games']
plt.axhline(y=0.0, color='k', linestyle='--', linewidth=1.0)
ticks_range = np.arange(min(games_all_in_period_list), max(games_all_in_period_list) + 1, ticks_2_interval)
plt.xticks(ticks_range)
plt.tick_params(axis='both', which='major', labelsize=ticks_font_size)
plt.title('FinalDQN victory statistics plot', fontsize=font_size)
plt.ylabel('Victories in period of 500 games', fontsize=font_size)
plt.xlabel('Episodes (games played)', fontsize=font_size)
plt.legend(legend_entries, loc='lower right', prop={'size': font_size})
plt.show()
































