import socket

from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator

SERVER_IP = "0.0.0.0"
SERVER_HOST_IP = socket.gethostbyname(socket.gethostname())


class Server:
    def __init__(self, menu):
        self.menu = menu
        self.validator = Validator()

    def handle_server_input(self, server_input: str):
        while True:
            if server_input == 'S':
                self.initialize_server_connection()
                break
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

    def initialize_server_connection(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            server_port = 50000
            # getting details about server and receiver
            #server_port = self.menu.get_port_input("receiver")
            server_details = (SERVER_IP, server_port)
            initial_header = Header(FlagEnum.ACK.value, 0, 0)

            # receiving response from the client
            received_flag, client_address = server_socket.recvfrom(1465)

            # sending initial_header to client
            server_socket.sendto(initial_header, server_details)

            # processing received data
            initial_header.flag = int.from_bytes(received_flag[:1], 'big')
            if initial_header.flag is FlagEnum.ACK.value:
                print(f"Connection initialized. Client details: {client_address}")
                self.server_sender(server_socket, client_address)
            else:
                print("Connection failed! Blabla")
        except Exception as e:
                print(f"An error occurred: {e}. Try again.")
                print("Connection failed!")

    def server_sender(self, server_socket, client_address):
        pass
