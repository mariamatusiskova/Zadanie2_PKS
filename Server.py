import os
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
        self.count_recv_dgram = 0
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

        # uncomment for testing purpose
        server_port = 50000

        try:
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
            if self.is_SYN(r_flag):
                print(f"Connection initialized. Client details: {client_address}")
                if server_socket is not None:
                    self.server_sender(server_socket, client_address)
                    return server_port
            else:
                print("Connection failed!")
        except Exception as e:
            print(f"An error occurred: {e}. Try again.")

    def initialize_message(self, flag: int, frag_order: int, data: bytes = b'') -> bytes:
        header = Header(flag, frag_order, self.crc.calculate(data))
        header_data = header.get_header_body()

        return header_data + data

    def server_sender(self, server_socket: socket, client_address: tuple):
        self.count_recv_dgram = 0
        save_frag_message = {}
        is_path = False
        convert_path_to_os = ""

        if server_socket is not None:
            while True:
                r_header = server_socket.recv(self.buff_size)
                r_flag, r_frag_order, r_crc, r_data = self.initialize_recv_header(r_header)

                if self.is_FIN(r_flag):
                    print("FIN, end of connection.")
                    print(f"{self.count_recv_dgram} fragments were received.")
                    server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, r_frag_order), client_address)
                    break

                if self.is_FILE(r_flag):
                    convert_path_to_os = os.path.normpath(r_data.decode('utf-8'))
                    is_path = True
                    print(f"path: {r_data}")
                    print(f"after convert: {convert_path_to_os}")

                if self.validator.is_crc_valid(r_data, r_crc, self.crc) and self.is_not_in_dict(r_frag_order, save_frag_message):
                    if self.is_DATA(r_flag):
                        print(f"received data: {r_data}")
                        save_frag_message[r_frag_order] = r_data
                        self.count_recv_dgram += 1
                    print(f"Received fragment of {r_frag_order}")
                    server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, r_frag_order), client_address)
                else:
                    print("Data received, but they are damaged or duplicated.")
                    server_socket.sendto(self.initialize_message(FlagEnum.NACK.value, r_frag_order), client_address)

            joined_data = b''.join([save_frag_message[frag_order] for frag_order in sorted(save_frag_message.keys())])

            # file message
            if is_path:
                self.save_file(convert_path_to_os, joined_data)
                return

            # text message
            self.print_text_message(joined_data)

    @staticmethod
    def print_text_message(joined_data: bytes):
        try:
            decoded_data = joined_data.decode('utf-8')
            print(decoded_data)
        except UnicodeDecodeError:
            print("Unable to decode data as UTF-8. This may not be a text file.")

    @staticmethod
    def save_file(convert_path_to_os: str, joined_data: bytes):
        try:
            path_dir, file_name = os.path.split(convert_path_to_os)

            if not os.path.exists(path_dir):
                os.makedirs(path_dir)

            absolute_path = os.path.abspath(convert_path_to_os)

            print(f"file_content:\n{joined_data}")

            # Save the data to the file
            with open(absolute_path, 'wb') as file:
                file.write(joined_data)

            print(f"File saved to: {absolute_path}")
            print(f'File name: {file_name}')
            print(f'File size: {os.path.getsize(absolute_path)}B')
        except Exception as e:
            print(f"Error saving file: {e}")

    @staticmethod
    def is_not_in_dict(r_frag_order: int, save_frag_message: dict) -> bool:
        return r_frag_order not in save_frag_message

    @staticmethod
    def is_FIN(r_flag) -> bool:
        return r_flag is FlagEnum.FIN.value

    @staticmethod
    def is_SYN(r_flag) -> bool:
        return r_flag is FlagEnum.SYN.value

    @staticmethod
    def is_FILE(r_flag) -> bool:
        return r_flag is FlagEnum.FILE.value

    @staticmethod
    def is_DATA(r_flag) -> bool:
        return r_flag is FlagEnum.DATA.value

    def initialize_recv_header(self, r_header: bytes) -> (int, int, int, bytes):
        return self.menu.get_flag(r_header), self.menu.get_frag_order(r_header), self.menu.get_crc(r_header), self.menu.get_data(r_header)
