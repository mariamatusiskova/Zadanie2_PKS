import sys
import socket

from Client import Client
from Server import Server
from Validator import Validator
from ColorPalette import ColorPalette as cp


class Menu:
    def __init__(self):
        self.validator = Validator()


    # check input of client, server or quit
    def handle_user_input(self, user_input: str):
        while True:
            if user_input == 'C':
                print(f"Running as client.")
                self.client_menu()
                break
            elif user_input == 'S':
                print(f"Running as server.")
                self.server_menu()
                break
            elif user_input == 'Q':
                self.quit_programme()
            else:
                print(f"{cp.YELLOW}Invalid input. Use 'C' as a client, 'S' as a server or 'Q' as quit.{cp.RESET}")
                self.menu()

    def menu(self):
        print('- [C] client')
        print('- [S] server')
        print('- [Q] quit')
        user_input = self.options()
        user_input = user_input.upper()
        print(f'Picked user_input: {user_input}')
        self.handle_user_input(user_input)

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

    # def client_menu(self):
    #     is_address = False
    #     server_ip = ""
    #     server_port = 0
    #     client_socket = None
    #
    #     try:
    #         while True:
    #             client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #
    #             if is_address:
    #                 print(f"- [S] continue as Client")
    #             else:
    #                 print('- [S] set the IP address and port of the receiver')
    #             print('- [RRM] switch role to server')
    #             print('- [Q] quit')
    #             client_input = self.options()
    #             client_input = client_input.upper()
    #             print(f'Picked client_input: {client_input}')
    #             client = Client(self)
    #             if is_address:
    #                 is_address, server_ip, server_port = client.handle_client_input(client_input, client_socket, server_ip, server_port)
    #             else:
    #                 is_address, server_ip, server_port = client.handle_client_input(client_input, client_socket)
    #     except Exception as e:
    #         print(f"{cp.YELLOW}Menu client: An error occurred: {e}. Try again.{cp.RESET}")
    #     finally:
    #         if client_socket:
    #             client_socket.close()

    def client_menu(self):
        is_address = False
        server_ip = ""
        server_port = 0
        client_socket = None

        try:
            while True:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                if is_address:
                    print(f"- [S] continue as Client")
                else:
                    print('- [S] set the IP address and port of the receiver')
                print('- [RRM] switch role to server')
                print('- [Q] quit')
                client_input = self.options()
                client_input = client_input.upper()
                print(f'Picked client_input: {client_input}')
                client = Client(self)
                if is_address:
                    is_address, server_ip, server_port = client.handle_client_input(client_input, client_socket, server_ip, server_port)
                else:
                    is_address, server_ip, server_port, client_socket = client.handle_client_input(client_input, client_socket)
        except Exception as e:
            print(f"{cp.YELLOW}Menu client: An error occurred: {e}. Try again.{cp.RESET}")
        # finally:
        #     if client_socket:
        #         client_socket.close()

    def server_menu(self):
        is_address = False
        server_port = 0
        server_socket = None

        try:
            while True:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                if is_address:
                    print(f"- [S] continue as Server")
                else:
                    print('- [S] set port of the server')
                print('- [RRM] switch role to client')
                print('- [Q] quit')
                server_input = self.options()
                server_input = server_input.upper()
                print(f'Picked server_input: {server_input}')
                server = Server(self)
                if is_address:
                    is_address, server_port = server.handle_server_input(server_input, server_socket, server_port)
                else:
                    is_address, server_port = server.handle_server_input(server_input, server_socket)
        except Exception as e:
            print(f"{cp.YELLOW}Menu server: An error occurred: {e}. Try again.{cp.RESET}")
        # finally:
        #     if server_socket:
        #         server_socket.close()
