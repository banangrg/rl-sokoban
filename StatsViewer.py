import os
import csv
import argparse
import numpy as np
import matplotlib.pyplot as plt
from SokobanGame import SokobanGame


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

    def get_str_with_new_lines(self):
        msg = "Index: " + str(self.index) + "\n" + self.map_name + "\nRotation: " + str(self.map_rotation) + \
              "\nStep count: " + str(self.number_of_steps) + ", Reward: " + "{0:.2f}".format(self.final_reward) + "\n"
        if self.was_victory:
            msg += "Victory"
        else:
            msg += "Loss"
        return msg


def read_all_game_stats_entries_from_file(file_name: str):
    stats_entry_counter = 0
    stats_entries = []

    with open(file_name, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            game_entry = GameStatsEntry(index=stats_entry_counter,
                                        map_name=row[0],
                                        map_rotation=int(row[1]),
                                        was_victory=str_to_bool(row[2]),
                                        number_of_steps=int(row[3]),
                                        final_reward=float(row[4]))
            stats_entries.append(game_entry)
            stats_entry_counter += 1

    return stats_entries, stats_entry_counter


def get_game_stats_entry_by_index(entry_list, index: int):
    for entry in entry_list:
        if entry.index == index:
            return entry
    return None


# python StatsViewer.py -f "game_stats/game_stats_dqn_v1_6000000_2019-05-12_04-52-04.txt" -m "VERY_SIMPLE_level.txt" -n 2000
if __name__ == "__main__":
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-f", "--stats_file", type=str, help="full path to game_stats file to load",
                             dest="stats_file",
                             default="game_stats/game_stats_dqn_v1_6000000_2019-05-12_04-52-04.txt")
    args_parser.add_argument("-m", "--map", type=str, help="name of map to show, can be partial, use all to allow all maps",
                             dest="map_name", default="VERY_SIMPLE_level.txt")
    args_parser.add_argument("-n", "--n_last", type=int,
                             help="number of entries to consider from the end (done before filtering on map name), if negative or 0 - all entries",
                             dest="n_last", default=0)
    args_parser.add_argument("-l", "--list_maps", help="if set lists all available map names",
                             action="store_true",
                             dest="list_maps")
    args_parser.add_argument("-d", "--detailed",
                             help="if set there will be points with hover action on figures, will look bad without some reasonabe -n value",
                             action="store_true",
                             dest="detailed")
    args_parser.add_argument("-wt", "--width", type=int,
                             help="width of figure window in inches",
                             dest="fig_width", default=14)
    args_parser.add_argument("-ht", "--height", type=int,
                             help="height of figure window in inches",
                             dest="fig_height", default=6)
    args = args_parser.parse_args()

    path_to_stats_file = args.stats_file
    map_name = args.map_name
    number_of_last_entries = args.n_last
    list_maps = args.list_maps
    detailed_figures = args.detailed
    figure_width = args.fig_width
    figure_height = args.fig_height

    use_number_of_last_entries = False
    if number_of_last_entries > 0:
        use_number_of_last_entries = True

    if map_name.upper() == 'all'.upper():
        map_name = ""

    if list_maps:
        print("-" * 50)
        print("Listing all available game maps:")
        for file in os.listdir(SokobanGame.PATH_TO_LEVELS):
            if not file.startswith("_"):    # ignore file with list of maps used by SokobanEnv
                print(file)
        print("-" * 50)

    entries, entry_counter = read_all_game_stats_entries_from_file(path_to_stats_file)

    # use only n last entries (-n option)
    if number_of_last_entries > entry_counter:
        print("[WARNING] n_last bigger than number of all entries - using all entries")
        use_number_of_last_entries = False
    if use_number_of_last_entries:
        entries = entries[-number_of_last_entries:]

    number_of_entries_after_n_last = len(entries)
    victories = [el for el in entries if el.was_victory]
    number_of_victories = len(victories)
    print("====== OVERVIEW STATS (ALL MAPS) =======")
    print("Loaded ", entry_counter, " entries from file ", path_to_stats_file)
    print("Total from " + str(number_of_entries_after_n_last) + " last games: " + str(number_of_victories) + "/" +
          str(number_of_entries_after_n_last) + " victories - " + str(number_of_victories / number_of_entries_after_n_last * 100.0) + "%")

    # filter on map name
    filtered_entries = [el for el in entries if map_name.upper() in el.map_name.upper()]
    number_of_filtered_entries = len(filtered_entries)
    filtered_victories = [el for el in filtered_entries if el.was_victory]
    if number_of_filtered_entries == 0:
        print("[ERROR] No games found on maps matching name: " + map_name)
        raise ValueError("Invalid map name specified")
    print("====== SPECIFIED MAP STATS =======")
    print("Found " + str(len(filtered_entries)) + " games played on map matching name: " + map_name)
    print(str(len(filtered_victories)) + "/" + str(number_of_filtered_entries) + " victories - " +
          str(len(filtered_victories) / number_of_filtered_entries * 100.0) + "%")

    # get values for plotting
    plot_x_values = np.arange(1, number_of_filtered_entries + 1)
    plot_y_values_rewards = [el.final_reward for el in filtered_entries]
    plot_y_values_steps = [el.number_of_steps for el in filtered_entries]

    # map x values to indexes of objects
    x_to_index = {}
    for i in range(number_of_filtered_entries):
        x_to_index[i + 1] = filtered_entries[i].index

    # configure figure window size
    plt.rcParams['figure.figsize'] = (figure_width, figure_height)

    fig = plt.figure()
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    # rewards
    if detailed_figures:
        rewards_points = ax1.scatter(plot_x_values, plot_y_values_rewards, marker='.', color='green')
    ax1.plot(plot_x_values, plot_y_values_rewards, color='green')
    ax1.axhline(y=0.0, color='r', linestyle='--', linewidth=0.5)
    ax1.set_title('Rewards')
    ax1.set_ylabel('Reward for episode')
    ax1.set_xlabel('Number of episode')

    # steps for episode
    if detailed_figures:
        steps_points = ax2.scatter(plot_x_values, plot_y_values_steps, marker='.', color='blue')
    ax2.plot(plot_x_values, plot_y_values_steps, color='blue')
    ax2.axhline(y=0.0, color='r', linestyle='--', linewidth=0.5)
    ax2.set_title('Number of steps for one episode')
    ax2.set_ylabel('Number of steps')
    ax2.set_xlabel('Number of episode')

    # annotations on mouse hover on point
    if detailed_figures:
        annot_rewards = ax1.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                                     bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot_steps = ax2.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                                   bbox=dict(boxstyle="round", fc="w"), arrowprops=dict(arrowstyle="->"))
        annot_rewards.set_visible(False)
        annot_steps.set_visible(False)

        # make annotations on top of figures
        fig.texts.append(ax1.texts.pop())
        fig.texts.append(ax2.texts.pop())

        def update_annot(ind, scatter_points, annot_obj, fig_obj):
            pos = scatter_points.get_offsets()[ind["ind"][0]]
            annot_obj.xy = pos
            index_of_stats_obj = x_to_index[int(pos[0])]    # first element of pos is x coord
            annot_msg = get_game_stats_entry_by_index(filtered_entries, index_of_stats_obj).get_str_with_new_lines()
            annot_obj.set_text(annot_msg)
            annot_obj.get_bbox_patch().set_alpha(0.99)  # non-transparent background
            annot_obj.set_visible(True)
            fig_obj.canvas.draw_idle()

        def hover(event):
            vis1 = annot_rewards.get_visible()
            vis2 = annot_steps.get_visible()
            cont1, ind1 = rewards_points.contains(event)
            cont2, ind2 = steps_points.contains(event)
            if cont1:
                update_annot(ind1, rewards_points, annot_rewards, fig)
            if cont2:
                update_annot(ind2, steps_points, annot_steps, fig)
            else:
                if vis1:
                    annot_rewards.set_visible(False)
                    fig.canvas.draw_idle()
                if vis2:
                    annot_steps.set_visible(False)
                    fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

    plt.show()
