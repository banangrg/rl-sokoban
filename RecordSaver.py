import datetime

import SobParams
from RewardDict import RewardDict


class RecordSaver:
    level_path = ""
    moves = []
    rewards = []

    @staticmethod
    def write_record():
        print("Write record")
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(RecordSaver.level_path)
        filename = RecordSaver.level_path + current_date + "." + SobParams.OUT_FILE_EXTENSION

        moves_string = SobParams.RECORD_DELIMITER.join(RecordSaver.moves)
        print(moves_string)

        rewards_string = SobParams.RECORD_DELIMITER.join(map(str, RecordSaver.rewards))
        rewards_string = rewards_string.replace("-0.05","")
        print(rewards_string)

        reward_sum = sum([float(reward) for reward in RecordSaver.rewards])
        print(reward_sum)
