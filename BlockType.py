from enum import Enum
import arcade


class BlockType(Enum):
    EMPTY = 0
    WALL = 1
    CHEST = 2
    GOAL = 3
    PLAYER = 4

    def get_color(self):
        return {
            BlockType.WALL: arcade.color.BLACK,
            BlockType.EMPTY: arcade.color.LIGHT_GREEN,
            BlockType.CHEST: arcade.color.LIGHT_BROWN,
            BlockType.GOAL: arcade.color.GREEN,
            BlockType.PLAYER: arcade.color.RED,
        }[self]