import datetime

import SobParams


class RecordSaver:
    record_path = ""
    moves = []
    rewards = []

    @staticmethod
    def write_record():
        print("Write record")
        current_date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        print(RecordSaver.record_path)
        RecordSaver.record_path = RecordSaver.record_path.split(".")[0]
        filename = RecordSaver.record_path + "_" + current_date + SobParams.OUT_FILE_EXTENSION

        moves_string = SobParams.RECORD_DELIMITER.join(RecordSaver.moves)
        print(moves_string)

        rewards_string = SobParams.RECORD_DELIMITER.join(map(str, RecordSaver.rewards))
        # rewards_string = rewards_string.replace("-0.05","")   - mozna latwiej sprawdzic czy wagi dobrze sie zapisuja
        print(rewards_string)

        reward_sum = sum([float(reward) for reward in RecordSaver.rewards])
        print(reward_sum)

        with open(filename, "w+") as f:
            f.write(RecordSaver.record_path + "\n")
            f.write(moves_string + "\n")
            f.write(rewards_string + "\n")
            f.write(str(reward_sum))
