import socket

from CRC32 import CRC32
from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator

# SERVER_IP = "0.0.0.0"
SERVER_IP = "localhost"
SERVER_HOST_IP = socket.gethostbyname(socket.gethostname())


class Server:
    def __init__(self, menu):
        self.buff_size = 1465
        self.menu = menu
        self.crc = CRC32()
        self.validator = Validator()

    def handle_server_input(self, server_input: str, server_port: int = 0) -> (bool, int):
        while True:
            if server_input == 'S':
                server_port = self.initialize_server_connection(server_port)
                return True, server_port
            elif server_input == 'RRM':
                print("Swapping roles.")
                # swap
                break
            elif server_input == 'Q':
                self.menu.quit_programme()
            else:
                print(
                    "Invalid input. Use 'S' as a settings of the server, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.server_menu()

    def initialize_server_connection(self, sent_server_port: int = 0) -> int:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            # uncomment for testing purpose
            server_port = 50000
            # getting details about server and receiver
            if sent_server_port:
                server_port = sent_server_port
            #else:
                # server_port = self.menu.get_port_input("receiver")
            server_details = (SERVER_HOST_IP, server_port)
            server_socket.bind(server_details)

            # receiving response from the client
            received_flag, client_address = server_socket.recvfrom(self.buff_size)
            # sending initial_header to client
            server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, 0), client_address)

            # processing received data
            r_flag = self.menu.get_flag(received_flag)
            if r_flag is FlagEnum.SYN.value:
                print(f"Connection initialized. Client details: {client_address}")
                self.server_sender(server_socket, client_address)
                return server_port
            else:
                print("Connection failed!")
        except Exception as e:
            print(f"An error occurred: {e}. Try again.")

    def initialize_message(self, flag: int, frag_order, data: bytes = b''):
        header = Header(flag, frag_order, self.crc.calculate(data))
        header_data = header.get_header_body()

        return header_data + data

    def server_sender(self, server_socket: socket, client_address: tuple):
        pass
