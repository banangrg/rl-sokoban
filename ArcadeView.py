import arcade

import SobParams as SobParams
from BlockType import BlockType


class ArcadeView(arcade.Window):

    def __init__(self, game_map):
        super().__init__(SobParams.WINDOW_WIDTH, SobParams.WINDOW_HEIGHT, SobParams.TITLE)

        self.listeners = []
        self.game_map = game_map

        arcade.draw_text("Hello", 0, 0, arcade.color.PINK, 24)
        # arcade.run()

    def on_draw(self):
        arcade.start_render()
        self.draw_map()

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
        arcade.draw_text(text, 0, 0, arcade.color.PINK, 24)

    def add_listener(self, listener):
        self.listeners.append(listener)
