import arcade

import SobParams as SobParams
from BlockType import BlockType


class ArcadeView(arcade.Window):

    def __init__(self, game_map):
        super().__init__(SobParams.WINDOW_WIDTH, SobParams.WINDOW_HEIGHT, SobParams.TITLE)

        self.listeners = []
        self.game_map = game_map
        self.shouldDisplayMessage = False
        self.message = "Default Message"

        arcade.start_render()
        arcade.set_background_color(SobParams.BACKGROUND_COLOR)

    def on_draw(self):
        self.draw_map()
        if self.shouldDisplayMessage:
            arcade.draw_text(self.message, 0, 0, arcade.color.PINK, 24)

    def on_key_press(self, key, modifiers):
        for listener in self.listeners:
            listener.on_key_press(key)

    def draw_field_at(self, x, y, block_type):
        arcade.draw_xywh_rectangle_filled(x * SobParams.FIELD_WIDTH, y * SobParams.FIELD_HEIGHT, SobParams.FIELD_WIDTH,
                                          SobParams.FIELD_HEIGHT,
                                          block_type.get_color())

    def draw_map(self):
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                self.draw_field_at(i, j, BlockType(self.game_map[i][j]))

    def draw_game_over(self, text):
        self.shouldDisplayMessage = True
        self.message = text

    def add_listener(self, listener):
        self.listeners.append(listener)
