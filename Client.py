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
                print("Invalid input. Use 'S' as a settings of the client, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.client_menu()

    def initialize_client_connection(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            server_ip, server_port = "10.10.51.142", 50000
            # getting details about server
            # server_ip, server_port = self.menu.get_ip_input("server/receiver"), self.menu.get_port_input(
            #     "server/receiver")
            server_details = (server_ip, server_port)
            initial_header = Header(FlagEnum.SYN.value, 0, 0)

            # sending initial_header to server
            client_socket.sendto(initial_header, server_details)

            # receiving response from the server
            received_flag, server_address = client_socket.recvfrom(1465)

            # processing received data
            initial_header.flag = int.from_bytes(received_flag[:1], 'big')
            if initial_header.flag is FlagEnum.ACK.value:
                print(f"Connection initialized. Server details: {server_address}")
                self.client_sender(client_socket, server_address)
            else:
                print("Connection failed!")
        except Exception as e:
            print(f"An error occurred: {e}. Try again.")
            print("Connection failed!")

    def client_sender(self, client_socket, server_address):
        while True:
            message_type = self.pick_text_or_file()

            if message_type == 'T':
                text_message = self.get_text_message_from_input()
                self.send_message(client_socket, server_address, message_type, text_message)
            elif message_type == 'F':
                file_message = self.get_file_message_from_input()
                self.send_message(client_socket, server_address, message_type, file_message)
            else:
                print("Invalid command!")

    def pick_text_or_file(self):
        print('- [F] file message')
        print('- [T] text message')
        message_type = self.menu.options()
        message_type = message_type.upper()
        print(f'Picked message_type: {message_type}')

        bool_value = self.validator.is_valid_message(message_type)

        if not bool_value:
            self.pick_text_or_file()

        return message_type

    def get_file_message_from_input(self):
        while True:
            file_path = str(input("Enter the path of the file to send: ")).encode('utf-8')

            try:
                with open(file_path, 'rb') as file_object:
                    file_content = file_object.read()
                    print(f'file content: {file_content}')
                    print(f'File name: {os.path.basename(file_path)}')
                    print(f'File size: {os.path.getsize(file_path)}B')
                    print(f'Absolute path: {os.path.abspath(file_path)}')
                    return file_content
            except FileNotFoundError:
                print("Didn't find the file. Try again.")
            except Exception as e:
                print(f"An error occurred: {e}. Try again.")

    def send_message(self, client_socket, server_address, message_type, message):
        pass

    @staticmethod
    def get_text_message_from_input():
        return str(input("Enter text message: ")).encode('utf-8')

