import sys

from Client import Client
from Server import Server
from Validator import Validator


class Menu:
    def __init__(self):
        self.validator = Validator()

    # check input of client, server or quit
    def handle_user_input(self, user_input: str):
        while True:
            if user_input == 'C':
                print("Running as client.")
                self.client_menu()
                break
            elif user_input == 'S':
                print("Running as server.")
                self.server_menu()
                break
            elif user_input == 'Q':
                self.quit_programme()
            else:
                print("Invalid input. Use 'C' as a client, 'S' as a server or 'Q' as quit.")
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
    def options():
        return input("Pick one from the options:")

    @staticmethod
    def quit_programme():
        print("The program exited.")
        sys.exit(1)

    def get_ip_input(self, role: str):
        while True:
            ip = input(f"Enter IP address of the {role}: ")
            if self.validator.is_valid_ip(ip):
                return ip
            else:
                print("Invalid IP address. Please enter a valid IP.")

    def get_port_input(self, role):
        while True:
            port = input(f"Enter port of the {role}: ")
            if self.validator.is_valid_port(port):
                return port
            else:
                print("Invalid port, should be in interval <0, 65 535>. Please enter a valid port.")

    def client_menu(self):
        print('- [S] set the IP address and port of the receiver')
        print('- [RRM] switch role to server')
        print('- [Q] quit')
        client_input = self.options()
        client_input = client_input.upper()
        print(f'Picked client_input: {client_input}')
        client = Client(self)
        client.handle_client_input(client_input)

    def server_menu(self):
        print('- [S] set port of the server')
        print('- [RRM] switch role to client')
        print('- [Q] quit')
        server_input = self.options()
        server_input = server_input.upper()
        print(f'Picked server_input: {server_input}')
        server = Server(self)
        server.handle_server_input(server_input)
