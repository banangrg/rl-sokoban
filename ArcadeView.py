import asyncio
import threading

import arcade

import SobParams as SobParams
import Utils
from BlockType import BlockType
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

    def on_draw(self):
        self.draw_map()
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

        for listener in self.listeners:
            listener.make_a_move(key)

    def draw_field_at(self, x, y, block_type):
        arcade.draw_xywh_rectangle_filled(y * SobParams.FIELD_WIDTH, x * SobParams.FIELD_HEIGHT, SobParams.FIELD_WIDTH,
                                          SobParams.FIELD_HEIGHT,
                                          block_type.get_color())

    def draw_map(self):
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                self.draw_field_at(len(self.game_map) - i - 1, j, BlockType(self.game_map[i][j]))

    def draw_game_over(self, text):
        self.shouldDisplayMessage = True
        self.message = text

    def add_listener(self, listener):
        self.listeners.append(listener)

    def restart(self):
        self.shouldDisplayMessage = False
        self.message = "Default Message"
