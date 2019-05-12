import os
import csv
import argparse
import numpy as np
import matplotlib.pyplot as plt
from SokobanGame import SokobanGame


PLOTS_WIDTH = 25   # in inches - due to matplotlib
PLOTS_HEIGHT = 10  # in inches


def str_to_bool(string: str):
    if string == 'True':
        return True
    elif string == 'False':
        return False
    else:
        raise ValueError("Invalid str to bool")


class GameStatsEntry:
    def __init__(self, index: int = -1, map_name: str = "NONE", map_rotation: int = -1, was_victory: bool = False,
                 number_of_steps: int = -1, final_reward: float = 0.0):
        self.index = index
        self.map_name = map_name
        self.map_rotation = map_rotation
        self.was_victory = was_victory
        self.number_of_steps = number_of_steps
        self.final_reward = final_reward

    def __str__(self):
        msg = str(self.index) + " - " + self.map_name + ", rotation = " + str(self.map_rotation) + \
              ", number of steps = " + str(self.number_of_steps) + ", final reward = " + str(self.final_reward) + ", "
        if self.was_victory:
            msg += "Victory"
        else:
            msg += "Loss"
        return msg


def read_all_game_stats_entries_from_file(file_name: str):
    stats_entry_counter = 0
    stats_entries = []

    with open(file_name, mode='r') as csv_file:
        csv_Rdr = csv.reader(csv_file, delimiter=';')
        for row in csv_Rdr:
            game_entry = GameStatsEntry(index=stats_entry_counter,
                                        map_name=row[0],
                                        map_rotation=int(row[1]),
                                        was_victory=str_to_bool(row[2]),
                                        number_of_steps=int(row[3]),
                                        final_reward=float(row[4]))
            stats_entries.append(game_entry)
            stats_entry_counter += 1

    return stats_entries, stats_entry_counter


# python StatsViewer.py -f "game_stats/game_stats_dqn_v1_6000000_2019-05-12_04-52-04.txt" -m "VERY_SIMPLE_level.txt" -n 2000
if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-f", "--stats_file", type=str, help="full path to game_stats file to load",
                             dest="stats_file",
                             default="game_stats/game_stats_dqn_v1_6000000_2019-05-12_04-52-04.txt")
    args_parser.add_argument("-m", "--map", type=str, help="name of map to show, can be partial",
                             dest="map_name", default="VERY_SIMPLE_level.txt")
    args_parser.add_argument("-n", "--n_last", type=int,
                             help="number of entries to consider from the end (done before filtering on map name), if negative or 0 - all entries",
                             dest="n_last", default=0)
    args_parser.add_argument("-l", "--list_maps", help="if set lists all available map names",
                             action="store_true",
                             dest="list_maps")
    args = args_parser.parse_args()

    path_to_stats_file = args.stats_file
    map_name = args.map_name
    number_of_last_entries = args.n_last
    list_maps = args.list_maps

    use_number_of_last_entries = False
    if number_of_last_entries > 0:
        use_number_of_last_entries = True

    if list_maps:
        print("-" * 50)
        print("Listing all available game maps:")
        for file in os.listdir(SokobanGame.PATH_TO_LEVELS):
            if not file.startswith("_"):    # ignore file with list of maps used by SokobanEnv
                print(file)
        print("-" * 50)

    entries, entry_counter = read_all_game_stats_entries_from_file(path_to_stats_file)

    # use onyl n last entries (-n option)
    if number_of_last_entries > entry_counter:
        print("[WARNING] n_last bigger than number of all entries - using all entries")
        use_number_of_last_entries = False
    if use_number_of_last_entries:
        entries = entries[-number_of_last_entries:]

    print("====== OVERVIEW STATS (ALL MAPS) =======")
    number_of_entries_after_n_last = len(entries)
    print("Loaded ", entry_counter, " entries from file ", path_to_stats_file)
    victories = [el for el in entries if el.was_victory]
    number_of_victories = len(victories)
    print("Total from " + str(number_of_entries_after_n_last) + " last games: " + str(number_of_victories) + "/" +
          str(number_of_entries_after_n_last) + " victories - " + str(number_of_victories / number_of_entries_after_n_last * 100.0) + "%")

    # filter on map name
    print("====== SPECIFIED MAP STATS =======")
    filtered_entries = [el for el in entries if map_name.upper() in el.map_name.upper()]
    number_of_filtered_entries = len(filtered_entries)
    if number_of_filtered_entries == 0:
        print("[ERROR] No games found on maps matching name: " + map_name)
        raise ValueError("Invalid map name specified")
    filtered_victories = [el for el in filtered_entries if el.was_victory]
    print("Found " + str(len(filtered_entries)) + " games played on map matching name: " + map_name)
    print(str(len(filtered_victories)) + "/" + str(number_of_filtered_entries) + " victories - " + str(len(filtered_victories) / number_of_filtered_entries * 100.0) + "%")

    plot_x_values = np.arange(1, number_of_filtered_entries + 1)
    plot_y_values_rewards = [el.final_reward for el in filtered_entries]
    plot_y_values_steps = [el.number_of_steps for el in filtered_entries]

    plt.rcParams['figure.figsize'] = (PLOTS_WIDTH, PLOTS_HEIGHT)

    plt.subplot(1, 2, 1)
    plt.plot(plot_x_values, plot_y_values_rewards, 'g')
    plt.axhline(y=0.0, color='r', linestyle='--', linewidth=1.0)
    plt.title('Rewards')
    plt.ylabel('Reward for episode')
    plt.xlabel('Number of episode')

    plt.subplot(1, 2, 2)
    plt.plot(plot_x_values, plot_y_values_steps, 'b')
    plt.axhline(y=0.0, color='r', linestyle='--', linewidth=1.0)
    plt.title('Number of steps for one episode')
    plt.ylabel('Number of steps')
    plt.xlabel('Number of episode')

    plt.show()
