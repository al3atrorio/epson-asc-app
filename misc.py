from enum import Enum, unique

@unique
class Direction(Enum):
    ToDojot = 1
    ToReaders = 2
    ToLeds = 3
    ToGpios = 4
    ToDisplays = 5
    ToLwm2m = 6
    InferDirection = 7
    Unknown = 8