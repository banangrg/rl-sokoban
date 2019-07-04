import time

import arcade

import SobParams as SobParams
from map_generator import Utils
from map_generator.BlockType import BlockType
from MoveEnum import MoveEnum


class ArcadeView(arcade.Window):

    def __init__(self, game_map):
        Utils.set_width_and_height(game_map)
        super().__init__(SobParams.WINDOW_HEIGHT, SobParams.WINDOW_WIDTH, SobParams.TITLE)

        self.game_map = game_map
        self.listeners = []
        self.restart()

        arcade.start_render()
        arcade.set_background_color(SobParams.BACKGROUND_COLOR)

    # def resize_window(self):
    #     Utils.set_width_and_height(self.game_map)
    #     # super().on_resize(SobParams.WINDOW_HEIGHT, SobParams.WINDOW_WIDTH)
    #     super().on_resize(600, 600)

    def on_draw(self):
        self.draw_map(self.game_map)
        if self.shouldDisplayMessage:
            arcade.draw_text(self.message, 0, 0, arcade.color.PINK, 24)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            print("left")
            key = MoveEnum.LEFT
        elif key == arcade.key.RIGHT:
            print("right")
            key = MoveEnum.RIGHT
        elif key == arcade.key.UP:
            print("up")
            key = MoveEnum.UP
        elif key == arcade.key.DOWN:
            print("down")
            key = MoveEnum.DOWN
        elif key == arcade.key.SPACE:
            print("Starting")
            for listener in self.listeners:
                listener.restart_with_next_inputs()

        for listener in self.listeners:
            listener.make_a_move(key)

    def draw_field_at(self, x, y, block_type):
        arcade.draw_xywh_rectangle_filled(y * SobParams.FIELD_WIDTH, x * SobParams.FIELD_HEIGHT, SobParams.FIELD_WIDTH,
                                          SobParams.FIELD_HEIGHT,
                                          block_type.get_color())

    def draw_map(self, game_map):
        # game_map = self.draw_all_walls()
        for i in range(len(game_map)):
            for j in range(len(game_map[i])):
                self.draw_field_at(len(game_map) - i - 1, j, BlockType(game_map[i][j]))

    def draw_game_over(self, text):
        self.shouldDisplayMessage = True
        self.message = text

    def add_listener(self, listener):
        self.listeners.append(listener)

    def get_all_walls_map(self):
        size = int(SobParams.WINDOW_HEIGHT / SobParams.FIELD_WIDTH)
        wall_map = []
        for i in range(0, size):
            line = []
            for j in range(0, size):
                line.append(BlockType.WALL.value)
            wall_map.append(line)
        # self.draw_map(wall_map)
        return wall_map

    def restart(self):
        game_map_backup = self.game_map
        self.game_map = self.get_all_walls_map()
        time.sleep(0.001)
        self.game_map = game_map_backup

        self.shouldDisplayMessage = False
        self.message = "Default Message"

    def draw_text(self, text):
        self.shouldDisplayMessage = True
        self.message = text
