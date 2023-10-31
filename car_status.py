from enum import Enum


class CarStatus(Enum):
    UNKNOWN = 0
    ENTERING = 1
    EXITING = 2
    PARKED = 3
    AWAY = 4
