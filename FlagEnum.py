from enum import Enum


class FlagEnum(Enum):
    SYN = 1
    ACK = 2
    NACK = 3
    FILE = 4
    DATA = 5
    KA = 6
    RRM = 7
    FIN = 8
