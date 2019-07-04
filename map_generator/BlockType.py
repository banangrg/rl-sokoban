from enum import Enum
import arcade


class BlockType(Enum):
    EMPTY = ' '
    WALL = '#'
    CHEST = '$'
    GOAL = '.'
    PLAYER = '@'
    CHEST_ON_GOAL = '*'
    PLAYER_ON_GOAL = '+'

    def get_color(self):
        return {
            BlockType.WALL: arcade.color.BLACK,
            BlockType.EMPTY: arcade.color.LIGHT_GREEN,
            BlockType.CHEST: arcade.color.LIGHT_BROWN,
            BlockType.GOAL: arcade.color.GREEN,
            BlockType.PLAYER: arcade.color.RED,
            BlockType.CHEST_ON_GOAL: arcade.color.PURPLE,
            BlockType.PLAYER_ON_GOAL: arcade.color.PINK
        }[self]
