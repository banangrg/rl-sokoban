import arcade

import Constants as cs
import BlockType
import Utils

player_position = []
game_map = Utils.generate_example_map()

arcade.open_window(cs.WINDOW_WIDTH, cs.WINDOW_HEIGHT, cs.TITLE)
arcade.set_background_color(cs.BACKGROUND_COLOR)
arcade.start_render()

# draw_field_at(0, 0, BlockType.CHEST)
# draw_field_at(4, 6, BlockType.CHEST)
player_position = Utils.draw_map(game_map)

arcade.finish_render()
arcade.run()
