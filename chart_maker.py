import os
import re
import sys
import numpy as np
import matplotlib.pyplot as plt


EXCLUDED_FILE_PREFIX = '__'
CHART_TICK_INTERVAL = 1000
CHART_MAKER_FILES_FIR = "chart_maker_files/"
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


# load files
files_to_load = [CHART_MAKER_FILES_FIR + file for file in os.listdir(CHART_MAKER_FILES_FIR) if not file.startswith(EXCLUDED_FILE_PREFIX)]
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
episodes_counters = []
episode_rewards_avg = []
episode_rewards_min = []
episode_rewards_max = []
rewards_avg = []
losses_avg = []
mae_avg = []
q_avg = []
for entry in entries:
    current_episodes_counter += int(re.findall(EPISODE_REGEX, entry)[0])
    episodes_counters.append(current_episodes_counter)
    episode_rewards_avg.append(float(re.findall(EPISODE_AVG_REWARD_REGEX, entry)[0]))
    episode_rewards_min.append(float(re.findall(EPISODE_MIN_REWARD_REGEX, entry)[0]))
    episode_rewards_max.append(float(re.findall(EPISODE_MAX_REWARD_REGEX, entry)[0]))
    if 'loss: ' in entry:
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

lists_to_plot = {
    'g-': episode_rewards_avg,
    'b-': episode_rewards_min,
    'r-': episode_rewards_max
}

plt.style.use('seaborn')
for item in lists_to_plot.items():
    plt.plot(episodes_counters, item[1], item[0])
legend_entries = ['average reward', 'min reward', 'max reward']
plt.axhline(y=0.0, color='k', linestyle='--', linewidth=2.0)
ticks_range = np.arange(min(episodes_counters), max(episodes_counters)+1, CHART_TICK_INTERVAL)
plt.xticks(ticks_range)
plt.title('FinalDQN rewards statistics plot')
plt.ylabel('Reward')
plt.xlabel('Episodes (games played)')
plt.legend(legend_entries, loc='lower right', prop={'size': 16})
plt.show()

plt.style.use('seaborn')
plt.plot(games_all_in_period_list, games_won_in_period_list, 'b-')
legend_entries = ['games won in period of 500 games']
plt.axhline(y=0.0, color='k', linestyle='--', linewidth=2.0)
ticks_range = np.arange(min(episodes_counters), max(episodes_counters)+1, CHART_TICK_INTERVAL)
plt.xticks(ticks_range)
plt.title('FinalDQN victory statistics plot')
plt.ylabel('Victories in period of 500 games')
plt.xlabel('Episodes (games played)')
plt.legend(legend_entries, loc='lower right', prop={'size': 16})
plt.show()
































