import sys

from map_generator import Utils
from RecordSaver import RecordSaver
from map_generator.SokobanGameEngine import SokobanGameEngine

class InputManager:

    def __init__(self):
        level_path = Utils.get_level_path(sys.argv)
        RecordSaver.record_path = Utils.get_record_path(sys.argv)
        game_map = Utils.read_map_from_file_path(level_path)
        self.sokobanGameEngine = SokobanGameEngine(game_map)