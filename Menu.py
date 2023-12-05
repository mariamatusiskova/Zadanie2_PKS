import sys
import socket

from Validator import Validator
from ColorPalette import color as cp


class Menu:
    def __init__(self):
        self.validator = Validator()

    def pick_text_or_file(self) -> str:
        print('- [F] file message')
        print('- [T] text message')
        message_type = self.options()
        message_type = message_type.upper()
        print(f'Picked message_type: {message_type}')

        bool_value = self.validator.is_valid_message(message_type)

        if bool_value is False:
            self.pick_text_or_file()
        return message_type

    @staticmethod
    def options() -> str:
        return input("Pick one from the options:")

    @staticmethod
    def quit_programme():
        print(f"The program exited.")
        sys.exit(1)

    def initialize_recv_header(self, r_header: bytes) -> (int, int, int, bytes):
        return self.get_flag(r_header), self.get_frag_order(r_header), self.get_crc(r_header), self.get_data(r_header)

    def get_ip_input(self, role: str) -> str:
        while True:
            ip = input(f"Enter IP address of the {role}: ")
            if self.validator.is_valid_ip(ip):
                return ip
            else:
                print(f"{cp.YELLOW}Invalid IP address. Please enter a valid IP.{cp.RESET}")

    def get_port_input(self, role: str) -> str:
        while True:
            port = input(f"Enter port of the {role}: ")
            if self.validator.is_valid_port(port):
                return port
            else:
                print(f"{cp.YELLOW}Invalid port, should be in interval <0, 65 535>. Please enter a valid port.{cp.RESET}")

    @staticmethod
    def get_flag(data) -> int:
        return int.from_bytes(data[:1], 'big')

    @staticmethod
    def get_frag_order(data) -> int:
        return int.from_bytes(data[1:3], 'big')

    @staticmethod
    def get_crc(data) -> int:
        return int.from_bytes(data[3:7], 'big')

    @staticmethod
    def get_data(data) -> bytes:
        return data[7:]

