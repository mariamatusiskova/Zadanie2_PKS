from enum import Enum


class FlagEnum(Enum):
    SYN = 1
    ACK = 2
    NACK = 3
    DATA = 4
    KA = 5
    RRM = 6
    FIN = 7
