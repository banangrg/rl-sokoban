from operator import add

import arcade

from ArcadeView import ArcadeView
import SobParams as cs
import Utils
from ArcadeViewListener import ArcadeViewListener
from BlockType import BlockType
from RecordSaver import RecordSaver
from RewardDict import RewardDict


class SobokanGameEngine(ArcadeViewListener):
    def __init__(self, game_map):
        super().__init__()

        self.arcadeView = ArcadeView(game_map)
        self.arcadeView.add_listener(self)

        self.game_map = game_map
        self.player_position = self.find_block_of_type(BlockType.PLAYER)
        self.goals_left = self.calculate_num_of_block_of_type(BlockType.GOAL)
        self.is_player_on_goal = False
        self.game_over = False
        self.moves = []
        self.record_saved = False
        self.rewards = []

    def on_draw(self):
        # self.draw_map()
        if self.game_over:
            self.draw_game_over()
            if not self.record_saved:
                RecordSaver.moves = self.moves
                RecordSaver.rewards = self.rewards
                RecordSaver.write_record()
                self.record_saved = True

    def on_key_press(self, key):
        # super.on_key_press(key)
        if self.game_over:
            return
        if key == arcade.key.LEFT:
            print("left")
            movement_array = [-1, 0]
            self.moves.append("L")
        elif key == arcade.key.RIGHT:
            print("right")
            movement_array = [1, 0]
            self.moves.append("R")
        elif key == arcade.key.UP:
            print("up")
            movement_array = [0, 1]
        elif key == arcade.key.DOWN:
            self.moves.append("U")
            print("down")
            movement_array = [0, -1]
            self.moves.append("L")

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

        if len(self.rewards) > cs.MOVE_TIMEOUT:
            self.game_over = True
            self.rewards.append(RewardDict.LOSS)

        self.on_draw()

    def draw_map(self):
        self.arcadeView.draw_map(self.game_map)
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
        if len(self.rewards) > cs.MOVE_TIMEOUT:
            output = "Failure"
        else:
            output = "Success"
        self.arcadeView.draw_game_over(output)
        arcade.draw_text(output, 0, 0, arcade.color.PINK, 24)
