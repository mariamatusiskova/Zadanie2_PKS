class Header:
    def __init__(self, flag, frag_order, crc):
        self.flag = flag.to_bytes(1, 'big')
        self.frag_order = frag_order.to_bytes(2, 'big')
        self.crc = crc.to_bytes(4, 'big')
