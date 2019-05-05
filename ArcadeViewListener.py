from abc import ABC, abstractmethod


class ArcadeViewListener(ABC):
    @abstractmethod
    def on_key_press(self):
        pass
