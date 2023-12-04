from enum import Enum


class FlagEnum(Enum):
    INF = 1
    ACK = 2
    ACK_KA = 3
    NACK = 4
    FILE = 5
    DATA = 6
    KA = 7
    RRM = 8
    FIN = 9
    END = 10
