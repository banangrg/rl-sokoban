import datetime

from map_generator import MapGeneratorConfig, Utils
from map_generator.MapGeneratorPlayerActionEnum import MapGeneratorPlayerActionEnum


def save_game_map(game_map, image=None):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    parameters = [MapGeneratorConfig.MAP_WIDTH, MapGeneratorConfig.MAP_HEIGHT,
                  MapGeneratorConfig.NUM_OF_CHESTS,
                  MapGeneratorConfig.NUM_OF_MOVES,
                  MapGeneratorPlayerActionEnum.PULL_CHEST.value,
                  MapGeneratorPlayerActionEnum.CHANGE_SIDE.value]
    file_name = MapGeneratorConfig.PATH_TO_MAPS + str(parameters) + "_" + current_date + ".txt"

    game_map_string = Utils.get_string_game_map(game_map)

    print("Saving map to: ", file_name)
    with open(file_name, "w+") as f:
        f.write(game_map_string)

    # image.save(file_name, "PNG")
