import socket

from ColorPalette import color


class Validator:
    def __init__(self):
        pass

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_port(port: str) -> bool:
        try:
            port = int(port)
            return 0 <= port <= 65535
        except ValueError:
            return False

    @staticmethod
    def is_valid_message(message_type: str) -> bool:
        if message_type == 'F':
            return True
        elif message_type == 'T':
            return True
        else:
            print(f"{color.YELLOW}Invalid input. Use 'F' as a file or 'M' as a text message.{color.RESET}")
            return False

    @staticmethod
    def is_valid_answer(answer: str) -> bool:
        if answer == 'Y':
            return True
        elif answer == 'N':
            return True
        else:
            print(f"{color.YELLOW}Invalid input. Use 'Y' as yes or 'N' as a no.{color.RESET}")
            return False

    @staticmethod
    def is_valid_fragment_size(fragment_size: int) -> bool:
        if fragment_size < 8:
            return False
        elif fragment_size > 1425:
            return False
        else:
            return True

    @staticmethod
    def is_crc_valid(r_data: bytes, r_crc: int, crc) -> bool:
        calculated_crc = crc.calculate(r_data)
        return calculated_crc == r_crc
