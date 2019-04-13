import arcade
import Constants as cs
from BlockType import BlockType


def draw_field_at(x, y, block_type):
    arcade.draw_xywh_rectangle_filled(x * cs.FIELD_WIDTH, y * cs.FIELD_HEIGHT, cs.FIELD_WIDTH, cs.FIELD_HEIGHT,
                                      block_type.get_color())


def generate_example_map():
    example_map = []

    top_row = []
    for i in range(0, 10):
        top_row.append(1)
    example_map.append(top_row)

    middle_row = [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    for i in range(0, 8):
        example_map.append(middle_row.copy())

    example_map.append(top_row.copy())
    example_map[4][8] = BlockType.PLAYER

    return example_map


def draw_map(map):
    print(type(map))
    for i in range(len(map)):
        for j in range(len(map[i])):
            if BlockType(map[i][j]) == BlockType.PLAYER:
                player_position = [i,j]
            draw_field_at(i, j, BlockType(map[i][j]))
    return player_position
