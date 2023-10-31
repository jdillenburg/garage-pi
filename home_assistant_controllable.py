from abc import ABC, abstractmethod


class HomeAssistantControllable(ABC):
    """These methods can be called by HomeAssistant."""
    @abstractmethod
    def set_park_distance(self, park_distance: float):
        pass

    @abstractmethod
    def open_or_close(self, reason: str):
        pass

