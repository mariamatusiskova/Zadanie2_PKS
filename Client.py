import math
import os
import socket

from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator


class Client:
    def __init__(self, menu):
        self.menu = menu
        self.validator = Validator()

    # menu for initializing connection
    def handle_client_input(self, client_input: str):
        while True:
            if client_input == 'S':
                self.initialize_client_connection()
                break
            elif client_input == 'RRM':
                print("Swapping roles.")
                # swap
                break
            elif client_input == 'Q':
                self.menu.quit_programme()
            else:
                print(
                    "Invalid input. Use 'S' as a settings of the client, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.client_menu()

    def initialize_client_connection(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            # uncomment for testing purpose
            server_ip, server_port = "localhost", 50000
            # getting details about server
            # server_ip, server_port = self.menu.get_ip_input("server/receiver"), self.menu.get_port_input(
            #     "server/receiver")
            server_details = (server_ip, server_port)
            # client_socket.bind("localhost", 50000) ??????????????????????????????????????????????????????????????????????????????????????????????????????
            initial_header = Header(FlagEnum.SYN.value, 0, 0)
            initial_data = initial_header.get_header_body()

            # sending initial_header to server
            client_socket.sendto(initial_data, server_details)

            # receiving response from the server
            received_flag, server_address = client_socket.recvfrom(1465)

            # processing received data
            initial_header.flag = int.from_bytes(received_flag[:1], 'big')
            if initial_header.flag is FlagEnum.ACK.value:
                print(f"Connection initialized. Server details: {server_address}")
                if client_socket is not None:
                    self.client_sender(client_socket, server_address)
            else:
                print("Connection failed!")
                print("Message: NACK\n Connection failed!")
        except Exception as e:
            print(f"An error occurred: {e}. Try again.")

    def pick_text_or_file(self) -> str:
        print('- [F] file message')
        print('- [T] text message')
        message_type = self.menu.options()
        message_type = message_type.upper()
        print(f'Picked message_type: {message_type}')

        bool_value = self.validator.is_valid_message(message_type)

        if bool_value is False:
            self.pick_text_or_file()
        return message_type

    def get_file_message_from_input(self) -> (bytes, str):
        while True:
            file_path = str(input("Enter the path of the file to send: "))
            convert_path_to_os = os.path.normpath(file_path)

            try:
                with open(convert_path_to_os, 'rb') as file_object:
                    file_content = file_object.read()
                    print(f'file content: {file_content}')
                    file_name = os.path.basename(convert_path_to_os)
                    print(f'File name: {file_name}')
                    print(f'File size: {os.path.getsize(convert_path_to_os)}B')
                    print(f'Absolute path: {os.path.abspath(convert_path_to_os)}')
                    return file_content, file_name
            except FileNotFoundError:
                print("Didn't find the file. Try again.")
            except Exception as e:
                print(f"An error occurred: {e}. Try again.")

    def client_sender(self, client_socket: socket, server_address: tuple):

        if client_socket is not None:
            while True:
                message_type = self.pick_text_or_file()

                if message_type == 'T':
                    text_message = self.get_text_message_from_input()
                    self.send_message(client_socket, server_address, message_type, text_message)
                elif message_type == 'F':
                    file_message, file_name = self.get_file_message_from_input()
                    self.send_message(client_socket, server_address, message_type, file_message, file_name)
                else:
                    print("Invalid command!")

    def send_message(self, client_socket, server_address, message_type, message, file_name=""):

        if client_socket is not None:
            fragment_size = self.get_fragment_size_input()

            if message_type == 'F':
                path_to_save_file = self.get_path_to_save_file(file_name)
                header = Header(FlagEnum.FILE.value, 0, 0)
                header_data = header.get_header_body()
                client_socket.sendto(header_data + path_to_save_file, server_address)

            dgrams_num = self.count_dgrams(message, fragment_size)



    def bad_datagram(self):
        print('- [Y] yes')
        print('- [N] no')
        answer = self.menu.options()
        answer = answer.upper()

        bool_value = self.validator.is_valid_answer(answer)

        if bool_value is False:
            self.bad_datagram()
        return answer

    def count_dgrams(self, message, fragment_size: int) -> int:
        return int(math.ceil(float(len(message)) / float(fragment_size)))

    def get_fragment_size_input(self) -> int:
        while True:
            try:
                fragment_size = int(input("Enter the size of the fragment, max: <8, 1425>: "))

                if self.validator.is_valid_fragment_size(fragment_size):
                    return fragment_size
                else:
                    print("Invalid input!")
            except ValueError:
                print("Invalid input! Please enter a valid integer.")

    def get_path_to_save_file(self, file_name: str) -> str:
        while True:
            path = input("Enter the path of the file to send: ")

            if os.path.isdir(path):
                return path + file_name
            else:
                print("Invalid path. Please enter a valid file path.")

    @staticmethod
    def get_text_message_from_input() -> bytes:
        return str(input("Enter text message: ")).encode('utf-8')
