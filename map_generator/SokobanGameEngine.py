import asyncio
import copy
import threading
import time
from operator import add

import arcade

import SobParams as SobParams
from map_generator import Utils
from ArcadeViewListener import ArcadeViewListener
from map_generator.BlockType import BlockType
from MoveEnum import MoveEnum
from RecordSaver import RecordSaver
from RewardDict import RewardDict
from map_generator.MovementArrayEnum import MovementArrayEnum


class AutoPlay(threading.Thread):
    def __init__(self, sokoban_game_engine, input_moves):
        super(AutoPlay, self).__init__()
        self.sokoban_game_engine = sokoban_game_engine
        self.input_moves = input_moves

    def run(self):
        self.input_moves = self.input_moves.split(SobParams.INPUT_MOVES_DELIMITER)
        for move in self.input_moves:
            print("Making a move")
            self.sokoban_game_engine.make_a_move(move)
            time.sleep(SobParams.MOVE_TIME_OFFSET)
        self.sokoban_game_engine.draw_game_over()
        self.sokoban_game_engine.restart_with_next_inputs()


class SokobanGameEngine(ArcadeViewListener):

    def __init__(self, game_map, arcade_view, input_moves_list=None, rotations=None):
        super().__init__()

        self.arcadeView = arcade_view
        self.arcadeView.restart()
        self.arcadeView.add_listener(self)

        self.original_map = game_map
        self.input_moves_list = input_moves_list
        self.input_moves_iterator = -1
        self.rotations = rotations

        # self.init_variables()
        # self.start_autoplay(input_moves_list[0])
        # self.restart_with_next_inputs()

        asyncio.run(arcade.run())

    def start_autoplay(self, input_moves):
        if input_moves is not None:
            self.autoplay_thread = AutoPlay(self, input_moves)
            self.autoplay_thread.start()

    def restart_with_next_inputs(self):
        self.input_moves_iterator += 1
        if self.input_moves_iterator >= len(self.input_moves_list):
            print("End of input moves")
        else:
            print("Staring input moves nr: ", self.input_moves_iterator)
            self.init_variables()
            self.start_autoplay(self.input_moves_list[self.input_moves_iterator])

    def init_variables(self):
        self.game_map = Utils.rotate_map(copy.deepcopy(self.original_map), self.rotations[self.input_moves_iterator])
        self.arcadeView.game_map = self.game_map
        # self.arcadeView.resize_window()
        self.arcadeView.restart()
        self.player_position = self.find_block_of_type(BlockType.PLAYER)
        self.goals_left = self.calculate_num_of_block_of_type(BlockType.GOAL)
        self.is_player_on_goal = False
        self.game_over = False
        self.moves = []
        self.record_saved = False
        self.rewards = []

    def check_if_game_over_and_handle_it(self):
        if self.game_over:
            self.draw_game_over()
            if not self.record_saved:
                RecordSaver.moves = self.moves
                RecordSaver.rewards = self.rewards
                RecordSaver.write_record()
                self.record_saved = True

    def make_a_move(self, key):
        if self.game_over:
            return
        if isinstance(key, MoveEnum):
            key = key.value
        if key == MoveEnum.LEFT.value:
            movement_array = MovementArrayEnum.LEFT.value
            self.arcadeView.draw_text("LEFT")
        elif key == MoveEnum.RIGHT.value:
            movement_array = MovementArrayEnum.RIGHT.value
            self.arcadeView.draw_text("RIGHT")
        elif key == MoveEnum.UP.value:
            movement_array = MovementArrayEnum.UP.value
            self.arcadeView.draw_text("UP")
        elif key == MoveEnum.DOWN.value:
            movement_array = MovementArrayEnum.DOWN.value
            self.arcadeView.draw_text("DOWN")
        self.moves.append(key)

        if self.get_player_next_field_type(movement_array) == BlockType.WALL:
            self.rewards.append(RewardDict.INVALID_MOVE)
            return
        elif self.get_player_next_field_type(movement_array) == BlockType.CHEST or self.get_player_next_field_type(
                movement_array) == BlockType.CHEST_ON_GOAL:
            chest_field = self.get_player_next_field(movement_array)
            after_chest_field = self.get_field_after(chest_field, movement_array)
            is_chest_on_goal = False
            if self.get_player_next_field_type(movement_array) == BlockType.CHEST_ON_GOAL:
                is_chest_on_goal = True
            if self.get_field_type(after_chest_field) == BlockType.CHEST or self.get_field_type(
                    after_chest_field) == BlockType.WALL:
                self.rewards.append(RewardDict.INVALID_MOVE)
                return
            elif self.get_field_type(after_chest_field) == BlockType.GOAL:

                self.move_player_and_chest(chest_field, movement_array, is_chest_on_goal, is_goal_next=True)
                self.goals_left -= 1
                self.rewards.append(RewardDict.BOX_ON_TARGET)
                if self.goals_left == 0:
                    print("Success")
                    self.game_over = True
                    self.rewards.append(RewardDict.VICTORY)
            else:
                self.move_player_and_chest(chest_field, movement_array, is_chest_on_goal)
                if is_chest_on_goal:
                    self.rewards.append(RewardDict.BOX_OFF_TARGET)
                else:
                    self.rewards.append(RewardDict.SIMPLE_MOVE)
        elif self.get_player_next_field_type(movement_array) == BlockType.GOAL:
            self.move_player(movement_array, is_goal_next=True)
            self.rewards.append(RewardDict.SIMPLE_MOVE)
        else:
            self.move_player(movement_array)
            self.rewards.append(RewardDict.SIMPLE_MOVE)

        if len(self.rewards) > SobParams.MOVE_TIMEOUT:
            self.game_over = True
            self.rewards.append(RewardDict.LOSS)

        self.check_if_game_over_and_handle_it()

    # def draw_map(self):
    #     self.arcadeView.draw_map(self.game_map)
        # for i in range(len(self.game_map)):
        #     for j in range(len(self.game_map[i])):
        #         ArcadeView.draw_field_at(i, j, BlockType(self.game_map[i][j]))

    def find_block_of_type(self, block_type):
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                if BlockType(self.game_map[i][j]) == block_type:
                    return [i, j]

    def calculate_num_of_block_of_type(self, block_type):
        num = 0
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                if BlockType(self.game_map[i][j]) == block_type:
                    num += 1
        return num

    def get_player_next_field(self, movement_array):
        return list(map(add, self.player_position, movement_array))

    def move_player(self, movement_array, is_goal_next=False):
        if self.is_player_on_goal:
            self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.GOAL
            self.is_player_on_goal = False
        else:
            self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.EMPTY
        self.player_position = self.get_player_next_field(movement_array)
        if is_goal_next:
            self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER_ON_GOAL
            self.is_player_on_goal = True
        else:
            self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER

    def get_player_next_field_type(self, movement_array):
        next_field = self.get_player_next_field(movement_array)
        return BlockType(self.game_map[next_field[0]][next_field[1]])

    def get_field_after(self, field, movement_array):
        return list(map(add, field, movement_array))

    def get_field_type(self, field):
        return BlockType(self.game_map[field[0]][field[1]])

    def move_player_and_chest(self, chest_field, movement_array, is_chest_on_goal, is_goal_next=False):
        self.move_player(movement_array, is_chest_on_goal)
        if is_chest_on_goal:
            self.goals_left += 1
        chest_field = self.get_field_after(chest_field, movement_array)
        if is_goal_next:
            self.game_map[chest_field[0]][chest_field[1]] = BlockType.CHEST_ON_GOAL
        else:
            self.game_map[chest_field[0]][chest_field[1]] = BlockType.CHEST

    def draw_game_over(self):
        # if len(self.rewards) > SobParams.MOVE_TIMEOUT:
        #     output = "Failure"
        # else:
        #     output = "Success"
        if self.goals_left != 0:
            output = "Failure"
        else:
            output = "Success"
        self.arcadeView.draw_game_over(output)
        # arcade.draw_text(output, 0, 0, arcade.color.PINK, 24)
        time.sleep(SobParams.FINISH_GAME_STOP_TIME)
        # self.arcadeView.close()
        # arcade.close_window()
        # raise Exception('End this game')
