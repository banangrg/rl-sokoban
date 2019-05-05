from abc import ABC, abstractmethod


class ArcadeViewListener(ABC):
    @abstractmethod
    def make_a_move(self):
        pass
