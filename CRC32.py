# Source: https://medium.com/@vbabak/implementing-crc32-in-typescript-ff3453a1a9e7

class CRC32:
    def __init__(self):
        # initial crc value
        self.crc = 0xFFFFFFFF
        # standard CRC32 polynomial
        self.poly = 0xEDB88320

    def calculate(self, data):
        # iterates through each byte in  the data
        for byte in data:
            # data XORed
            self.crc ^= byte
            # through the 1B = 8 bits
            for _ in range(8):
                # -1 nothing, otherwise it is 0 or 1
                mask = -(self.crc & 1)
                # shift to right
                self.crc = (self.crc >> 1) ^ (self.poly & mask)
        # XOR
        return self.crc ^ 0xFFFFFFFF
