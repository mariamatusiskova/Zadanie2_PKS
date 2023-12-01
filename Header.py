class Header:
    def __init__(self, flag: int, frag_order: int, crc: int):
        self.flag = flag.to_bytes(1, 'big')
        self.frag_order = frag_order.to_bytes(2, 'big')
        self.crc = crc.to_bytes(4, 'big')

    def get_header_body(self):
        return self.flag + self.frag_order + self.crc
