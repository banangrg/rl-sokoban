from abc import ABC, abstractmethod


class ArcadeViewListener(ABC):
    @abstractmethod
    def make_a_move(self):
        pass

    @abstractmethod
    def restart_with_next_inputs(self):
        pass
