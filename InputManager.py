from SobokanGameEngine import SobokanGameEngine
import sys

import SobParams as cs
import Utils
from RecordSaver import RecordSaver
from SobokanGameEngine import SobokanGameEngine

class InputManager:

    def __init__(self):
        level_path = Utils.get_level_path(sys.argv)
        RecordSaver.record_path = Utils.get_record_path(sys.argv)
        game_map = Utils.read_map_from_file_path(level_path)
        self.sobokanGameEngine = SobokanGameEngine(game_map)