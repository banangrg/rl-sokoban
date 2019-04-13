import arcade
import Constants as cs
from BlockType import BlockType
import Utils


class SobokanGame(arcade.Window):
    def __init__(self, width, height, title, game_map):
        super().__init__(width, height, title)

        self.game_map = game_map
        self.player_position = self.find_player_position()
        arcade.set_background_color(cs.BACKGROUND_COLOR)

    def on_draw(self):
        arcade.start_render()
        self.draw_map()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            print("left")
            if BlockType(self.game_map[self.player_position[0] - 1][self.player_position[1]]) != BlockType.WALL:
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.EMPTY
                self.player_position[0] -= 1
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER
        elif key == arcade.key.RIGHT:
            print("right")
            if BlockType(self.game_map[self.player_position[0] + 1][self.player_position[1]]) != BlockType.WALL:
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.EMPTY
                self.player_position[0] += 1;
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER
        elif key == arcade.key.UP:
            print("up")
            if BlockType(self.game_map[self.player_position[0]][self.player_position[1] + 1]) != BlockType.WALL:
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.EMPTY
                self.player_position[1] += 1;
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER
        elif key == arcade.key.DOWN:
            print("down")
            if BlockType(self.game_map[self.player_position[0]][self.player_position[1] - 1]) != BlockType.WALL:
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.EMPTY
                self.player_position[1] -= 1;
                self.game_map[self.player_position[0]][self.player_position[1]] = BlockType.PLAYER

    def draw_map(self):
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                Utils.draw_field_at(i, j, BlockType(self.game_map[i][j]))

    def find_player_position(self):
        for i in range(len(self.game_map)):
            for j in range(len(self.game_map[i])):
                if BlockType(self.game_map[i][j]) == BlockType.PLAYER:
                    player_position = [i, j]
        return player_position
