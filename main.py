# importing necessary modules
import socket
import sys

# importing custom classes and enums
from FlagEnum import FlagEnum
from Header import Header


# def check_server_input(server_input: str):
#     while True:
#         if server_input == 'client':
#             print("Running as client.")
#             client()
#             break
#         elif server_input == 'server':
#             print("Running as server.")
#             server()
#             break
#         elif server_input == 'quit':
#             quit_programme()
#         else:
#             print("Invalid input. Use 'client' or 'server'.")
#
#
# def server_menu():
#     pass
#
#
# def server():
#     # in the settings
#     #   listening
#     # switch role
#     # quit
#     pass


def handle_client_input(client_input: str):
    while True:
        if client_input == 'S':
            initialize_client()
            break
        elif client_input == 'RRM':
            print("Swapping roles.")
            # swap
            break
        elif client_input == 'Q':
            quit_programme()
        else:
            print("Invalid input. Use 'S' as a settings of the client, 'RRM' as a role reversal message or 'Q' as quit.")
            client_menu()


def client_menu():
    print('- [S] set the IP address and port of the receiver')
    print('- [RRM] switch role to server')
    print('- [Q] quit')
    client_input = options()
    client_input = client_input.upper()
    print(f'Picked client_input: {client_input}')
    handle_client_input(client_input)


def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def get_ip(role: str):
    while True:
        ip = input(f"Enter IP address of the {role}: ")
        if is_valid_ip(ip):
            return ip
        else:
            print("Invalid IP address. Please enter a valid IP.")


def is_valid_port(port):
    try:
        port = int(port)
        return 0 <= port <= 65535
    except ValueError:
        return False


def get_port(role):
    while True:
        port = input(f"Enter port of the {role}: ")
        if is_valid_port(port):
            return port
        else:
            print("Invalid port, should be in interval <0, 65 535>. Please enter a valid port.")


def initialize_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # getting details about server
        server_ip, server_port = get_ip("server/receiver"), get_port("server/receiver")
        server_details = (server_ip, server_port)
        initial_header = Header(FlagEnum.SYN, 0, 0)

        # sending initial_header to server
        client_socket.sendto(initial_header, server_details)

        # receiving response from the server
        received_flag, server_details = client_socket.recvfrom(1500)

        # processing received data
        initial_header.flag = int.from_bytes(received_flag[:1], 'big')
        if initial_header.flag is FlagEnum.ACK:
            print(f"Connection initialized. Server details: {server_details}")

        else:
            print("Connection failed!")
    except:
        print("Connection failed!")


def quit_programme():
    print("The program exited.")
    sys.exit(1)


# check input of client, server or quit
def handle_user_input(user_input: str):
    while True:
        if user_input == 'C':
            print("Running as client.")
            client_menu()
            break
        elif user_input == 'S':
            print("Running as server.")
            # server_menu()
            break
        elif user_input == 'Q':
            quit_programme()
        else:
            print("Invalid input. Use 'C' as a client, 'S' as a server or 'Q' as quit.")
            menu()


def options():
    return input("Pick one from the options:")


def menu():
    print('- [C] client')
    print('- [S] server')
    print('- [Q] quit')
    user_input = options()
    user_input = user_input.upper()
    print(f'Picked user_input: {user_input}')
    handle_user_input(user_input)


if __name__ == '__main__':
    menu()
