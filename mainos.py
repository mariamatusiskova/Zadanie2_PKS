import math
import time
import os
import socket
import threading
import random

from CRC32 import CRC32
from ColorPalette import color
from FlagEnum import flag_enum
from Header import Header
from Menu import Menu
from Validator import Validator

CLIENT_IP ="0.0.0.0"
CLIENT_PORT=5002

SERVER_IP="127.0.0.1"
SERVER_PORT=5000

MAX_FRAGMENT_SIZE=1465
MAX_SIZE_NO_HEADER=MAX_FRAGMENT_SIZE-13

BUFF_SIZE=1465

KEEPALIVE_EVENT=threading.Event()
RECEIVE_EVENT=threading.Event()
MAIN_EVENT=threading.Event()
LOCK = threading.Lock()

SWAP_ROLES=False


def print_text_message(joined_data: bytes):
    try:
        decoded_data = joined_data.decode('utf-8')
        print(decoded_data)
    except UnicodeDecodeError:
        print(f"{color.RED}Unable to decode data as UTF-8. This may not be a text file.{color.RESET}")


def save_file(convert_path_to_os: str, joined_data: bytes):
    try:
        path_dir, file_name = os.path.split(convert_path_to_os)

        if not os.path.exists(path_dir):
            os.makedirs(path_dir)

        absolute_path = os.path.abspath(convert_path_to_os)

        print(f"file_content:\n{joined_data}")

        CHUNK_SIZE = 4096
        with open(absolute_path, 'wb') as file:
            for i in range(0, len(joined_data), CHUNK_SIZE):
                chunk = joined_data[i:i + CHUNK_SIZE]
                file.write(chunk)

        print(f"File saved to: {absolute_path}")
        print(f'File name: {file_name}')
        print(f'File size: {os.path.getsize(absolute_path)}B')
    except Exception as e:
        print(f"{color.RED}Error saving file: {e} {color.RESET}")


def is_not_in_dict(r_frag_order: int, save_frag_message: dict) -> bool:
    return r_frag_order not in save_frag_message


def is_FIN(r_flag) -> bool:
    return r_flag is flag_enum.FIN.value


def is_INF(r_flag) -> bool:
    return r_flag is flag_enum.INF.value


def is_FILE(r_flag) -> bool:
    return r_flag is flag_enum.FILE.value


def is_END(r_flag) -> bool:
    return r_flag is flag_enum.END.value


def is_KA(r_flag) -> bool:
    return r_flag is flag_enum.KA.value


def are_DATA(r_flag) -> bool:
    return r_flag is flag_enum.DATA.value


def create_header_of_fragment(flag: int, frag_order: int, data: bytes = b'', crc: int = 0):
    if not crc:
        t_crc = CRC32()
        crc = t_crc.calculate(data)

    header = Header(flag, frag_order, crc)
    header_data = header.get_header_body()

    return header_data + data


def count_dgrams(buffer, fragment_size):
    print(f"len of message: {len(buffer)}")
    print(f"number of fragments: {int(math.ceil(float(len(buffer)) / float(fragment_size)))}")
    return int(math.ceil(float(len(buffer)) / float(fragment_size)))


def get_path_to_save_file(file_name: str) -> str:
    while True:
        path = input("Enter the path of the file to send: ")

        if os.path.isdir(path):
            return path + file_name
        else:
            print(f"{color.YELLOW}Invalid path. Please enter a valid file path.{color.RESET}")


def get_text_message_from_input() -> bytes:
    return str(input("Enter text message: ")).encode('utf-8')


def is_ACK(r_flag) -> bool:
    return r_flag is flag_enum.ACK.value


def is_ACK_KA(r_flag) -> bool:
    return r_flag is flag_enum.ACK_KA.value


def is_NACK(r_flag: int) -> bool:
    return r_flag is flag_enum.NACK.value


def get_file_message_from_input() -> (bytes, str):
    while True:
        file_path = str(input("Enter the path of the file to send: "))
        convert_path_to_os = os.path.normpath(file_path)

        try:
            CHUNK_SIZE = 4096
            chunks_list = []
            with open(convert_path_to_os, 'rb') as file_object:

                while True:
                    chunk = file_object.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    chunks_list.append(chunk)

            file_content = b''.join(chunks_list)
            file_name = os.path.basename(convert_path_to_os)
            print(f'File name: {file_name}')
            print(f'File size: {os.path.getsize(convert_path_to_os)}B')
            print(f'Absolute path: {os.path.abspath(convert_path_to_os)}')
            print(f"len of file content: {len(file_content)}")

            jpeg_start = file_content.find(b'\xff\xd8\xff')
            if jpeg_start != -1:
                path_length = len(file_path.encode())
                binary_data_start = file_content.find(file_path.encode()) + path_length

                if binary_data_start != -1:
                    file_content = file_content[binary_data_start:]

            return file_content, file_name
        except FileNotFoundError:
            print(f"{color.RED}Didn't find the file. Try again.{color.RESET}")
        except Exception as e:
            print(f"{color.RED}An error occurred: {e}. Try again.{color.RESET}")


class Client(threading.Thread):
    sock = None
    buffer = []
    global CLIENT_IP, CLIENT_PORT

    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((CLIENT_IP, CLIENT_PORT))

        print(f"CLIENT: {color.MAGENTA}( {CLIENT_IP},{CLIENT_PORT} ){color.RESET}")

        self.keepalive_thread = threading.Thread(target=self.keepalive_client_side)
        self.keepalive_thread.start()

    def keepalive_client_side(self):
        self.sock.settimeout(10)

        while not KEEPALIVE_EVENT.is_set():
            try:
                flag = int.to_bytes(flag_enum.KA.value, byteorder="big")
                self.sock.sendto(flag, (SERVER_IP, SERVER_PORT))

                try:
                    data = self.sock.recv(MAX_FRAGMENT_SIZE)

                    #print(f"{color.CYAN}keepalive_client_side: printing data (flag){color.RESET}")
                    #print(f"{color.CYAN}{Menu.get_flag(data)}{color.RESET}")

                    if int.from_bytes(data, byteorder="big") == flag_enum.ACK_KA.value:
                        #print(f"{color.GREEN}keepalive_client_side: ACK_KA RECEIVED{color.RESET}")
                        time.sleep(5)

                except socket.timeout:
                    print(f"{color.RED}keepalive_client_side: Timout reached on client keepalive{color.RESET}")
                    continue

            except socket.timeout:
                print(f"{color.RED}keepalive_client_side: No ACK received in a while ...{color.RESET}")
                MAIN_EVENT.set()
                KEEPALIVE_EVENT.set()
                return

    def switch_up_keepalive(self):
        MAIN_EVENT.clear()
        KEEPALIVE_EVENT.clear()

        self.keepalive_thread = threading.Thread(target=self.keepalive_client_side)
        self.keepalive_thread.start()

    def switch_down_keepalive(self):
        self.sock.settimeout(0.5)
        KEEPALIVE_EVENT.set()
        time.sleep(0.5)

        self.sock.sendto(bytes(0), (CLIENT_IP, CLIENT_PORT))
        self.keepalive_thread.join()
        self.sock.settimeout(None)

    def run(self):
        while not MAIN_EVENT.is_set():
            input_choice = 0

            while input_choice != 1 and input_choice != 2 and input_choice != 3 and input_choice != 4 and input_choice != 5:
                try:
                    input_choice = int(input(
                        f"<{color.ORANGE} [1] Send message/file {color.RESET}>\n<{color.ORANGE} [2] Swap roles {color.RESET}>\n<{color.ORANGE} [3] Exit {color.RESET}>\n\n___________________\n"))
                except ValueError:
                    print(f"{color.RED} ! BAD INPUT ! {color.RESET}")

            if input_choice == 1:
                self.initialize_client_connection()
            elif input_choice == 2:
                self.swap_roles()
            elif input_choice == 3:
                Menu.quit_programme()

    def initialize_client_connection(self):
        try:
            # sending initial_header to server
            self.sock.sendto(create_header_of_fragment(flag_enum.INF.value, 0), (SERVER_IP,SERVER_PORT))

            r_data = self.sock.recv(BUFF_SIZE)

            # processing received data
            r_flag = Menu.get_flag(r_data)
            if is_ACK(r_flag):
                self.client_sender()
            else:
                print(f"{color.CYAN}initialize_client_connection:{color.RESET} Connection failed!")
                print(f"{color.CYAN}initialize_client_connection:{color.RESET} Message: NACK\n Connection failed!")
        except Exception as e:
            print(f"{color.CYAN}initialize_client_connection:{color.RESET} An error occurred: {e}. Try again.")

    def client_sender(self):
        while True:
            menu = Menu()
            message_type = menu.pick_text_or_file()

            if message_type == 'T':
                text_message = get_text_message_from_input()
                self.send_message_s_and_w(message_type, text_message)
                break
            elif message_type == 'F':
                file_message, file_name = get_file_message_from_input()
                self.send_message_s_and_w(message_type, file_message, file_name)
                break
            else:
                print(f"{color.RED}Invalid command!{color.RESET}")

    def send_message_s_and_w(self, message_type: str, message: bytes, file_name: str = ""):
        global MAX_FRAGMENT_SIZE, MAX_SIZE_NO_HEADER
        frag_order = 0

        self.switch_down_keepalive()
        MAX_FRAGMENT_SIZE = int(input(f"{color.PINK}Set max fragment size: {color.RESET}"))

        # Ensure the minimum fragment size is 8 (less possible value)
        if MAX_FRAGMENT_SIZE < 8: MAX_FRAGMENT_SIZE = 8

        # Calculate the maximum size of the data payload in each fragment
        MAX_SIZE_NO_HEADER = MAX_FRAGMENT_SIZE - 7

        if message_type == 'F':
            path_to_save_file = get_path_to_save_file(file_name)

            print(f"Sending the file path to the server.")
            self.sock.sendto(create_header_of_fragment(flag_enum.FILE.value, frag_order, path_to_save_file.encode('utf-8')), (SERVER_IP,SERVER_PORT))

            r_data = self.sock.recv(BUFF_SIZE)
            r_flag = Menu.get_flag(r_data)

            if is_ACK(r_flag):
                print(f"Acknowledgment received. Sending the file to the server.")
            else:
                print(f"{color.RED}Error: Didn't receive ACK. Unable to complete the operation.{color.RESET}")
                return

        dgrams_num = count_dgrams(message, MAX_SIZE_NO_HEADER)
        bad_dgram = self.create_bad_datagram(dgrams_num)

        while self.all_dgrams_send(dgrams_num, frag_order):
            split_message = message[:MAX_SIZE_NO_HEADER]
            is_exit = False
            frag_order += 1

            attempt_count = 0
            while self.all_attempts(attempt_count, 3):
                if is_exit:
                    message = message[MAX_FRAGMENT_SIZE:]
                    break

                if self.is_bad_dgram(bad_dgram, frag_order):
                    self.sock.sendto(create_header_of_fragment(flag_enum.DATA.value, frag_order, split_message) + bytes(101), (SERVER_IP,SERVER_PORT))
                else:
                    self.sock.sendto(create_header_of_fragment(flag_enum.DATA.value, frag_order, split_message), (SERVER_IP,SERVER_PORT))

                print(f" - Sent fragment of {frag_order} - Size: {len(split_message)} bytes")

                try:
                    while True:
                        self.sock.settimeout(30)

                        r_data = self.sock.recv(BUFF_SIZE)

                        r_flag = Menu.get_flag(r_data)
                        r_frag_order = Menu.get_frag_order(r_data)

                        if self.is_not_valid_dgrams(r_frag_order, frag_order):
                            print(f"Duplicated, fragment {r_frag_order}.")
                            attempt_count += 1
                            continue

                        if is_NACK(r_flag):
                            print(f"NACK: Damaged message.")
                            attempt_count += 1
                            break

                        if self.is_all(dgrams_num, frag_order):
                            print(f"{frag_order} fragments were sent.")
                            self.sock.sendto(create_header_of_fragment(flag_enum.FIN.value, 0), (SERVER_IP,SERVER_PORT))

                        attempt_count = 0
                        is_exit = True
                        break

                except socket.timeout:
                    print(f"{color.YELLOW}Timeout! Sending packet again.{color.RESET}")
                    attempt_count += 1

            if attempt_count == 3:
                print(f"{color.RED}Maximum attempts reached. Unable to complete the operation.{color.RESET}")
                print(f"Last sent fragment was {frag_order} - Size: {len(split_message)} bytes")
                self.sock.sendto(create_header_of_fragment(flag_enum.END.value, 0), (SERVER_IP,SERVER_PORT))
                break

    def all_dgrams_send(self, dgrams_num, frag_order):
        return frag_order < dgrams_num

    def is_all(self, dgrams_num, frag_order):
        return frag_order == dgrams_num

    def is_not_valid_dgrams(self, r_frag_order, frag_order):
        return r_frag_order != frag_order

    def bad_datagram_input(self):
        print(f"Do you want to send a bad fragment during conversation?")
        print('- [Y] yes')
        print('- [N] no')
        answer = Menu.options()
        answer = answer.upper()

        bool_value = Validator.is_valid_answer(answer)

        if bool_value is False:
            self.bad_datagram_input()
        return answer

    def all_attempts(self, attempt_count, attempts):
        return attempt_count < attempts

    def is_bad_dgram(self, bad_dgram_num, frag_order):
        return frag_order == bad_dgram_num

    def create_bad_datagram(self, dgrams_num):
        option = self.bad_datagram_input()
        return random.randint(1, dgrams_num) if option == 'Y' else 0


class Server(threading.Thread):
    sock = None
    data_buffer = []
    global CLIENT_IP, CLIENT_PORT

    def __init__(self):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((SERVER_IP, SERVER_PORT))

        print(f"SERVER: {color.MAGENTA}({SERVER_IP},{SERVER_PORT}){color.RESET}")

        self.keepalive_thread = threading.Thread(target=self.keepalive_server_side)
        self.keepalive_thread.start()

    def keepalive_server_side(self):
        global CLIENT_IP, CLIENT_PORT
        self.sock.settimeout(10)

        while not KEEPALIVE_EVENT.is_set():
            try:
                data, client_data = self.sock.recvfrom(BUFF_SIZE)
                CLIENT_IP = client_data[0]
                CLIENT_PORT = client_data[1]

                #print(f"{color.CYAN}{str(data)}{color.RESET}")

                if int.from_bytes(data, byteorder="big") == flag_enum.KA.value:
                    #print(f"{color.GREEN}KA RECEIVED{color.RESET}")

                    flag = int.to_bytes(flag_enum.ACK_KA.value, byteorder="big")
                    self.sock.sendto(flag, (CLIENT_IP, CLIENT_PORT))

                    continue
            except socket.timeout:
                print(f"{color.RED}No ACK received in a while ...{color.RESET}")

                MAIN_EVENT.set()
                KEEPALIVE_EVENT.set()

                return

    def switch_up_keepalive(self):
        MAIN_EVENT.clear()
        KEEPALIVE_EVENT.clear()

        self.keepalive_thread = threading.Thread(target=self.keepalive_server_side)
        self.keepalive_thread.start()

    def switch_down_keepalive(self):
        self.sock.settimeout(0.5)
        KEEPALIVE_EVENT.set()
        self.sock.sendto(bytes(0), (SERVER_IP, SERVER_PORT))

        time.sleep(0.5)

        self.keepalive_thread.join()
        self.sock.settimeout(None)

    def receive_up(self):
        RECEIVE_EVENT.clear()
        self.receive_thread = threading.Thread(target=self.receiver)
        self.receive_thread.start()

    def receive_down(self):
        RECEIVE_EVENT.set()
        self.receive_thread.join()

    def run(self):
        input_choice = 0

        while not MAIN_EVENT.is_set():
            while True:
                try:
                    input_choice = int(input(
                        f"<{color.ORANGE} [1] Receive {color.RESET}>\n<{color.ORANGE} [2] Swap roles {color.RESET}>\n<{color.ORANGE} [3] Exit {color.RESET}>\n\n___________________\n"))

                    # Check if the entered choice is within the valid range
                    if 1 <= input_choice <= 3:
                        break
                    else:
                        print(f"{color.RED} ! Invalid choice. Please enter a number between 1 and 3. {color.RESET}")

                except ValueError:
                    print(f"{color.RED} ! Invalid input. Please enter a valid number. {color.RESET}")

            if input_choice == 1:
                self.initialize_server_connection()
            elif input_choice == 2:
                self.swap_roles()
            elif input_choice == 3:
                Menu.quit_programme()

    def initialize_server_connection(self):
        try:
            # receiving response from the client
            r_data = self.sock.recv(BUFF_SIZE)

            # sending initial_header to client
            self.sock.sendto(create_header_of_fragment(flag_enum.ACK.value, 0), (CLIENT_IP,CLIENT_PORT))

            # processing received data
            r_flag = Menu.get_flag(r_data)

            if is_INF(r_flag):
                self.receiver()
            else:
                print(f"{color.RED}Connection failed!{color.RESET}")
        except Exception as e:
            print(f"{color.RED}initialize_server_connection: An error occurred: {e}. Try again.{color.RESET}")

    def receiver(self):
        global MAX_FRAGMENT_SIZE
        self.sock.settimeout(None)

        count_recv_dgram = 0
        save_frag_message = {}
        is_path = False
        convert_path_to_os = ""
        crc = CRC32()
        menu = Menu()

        self.switch_down_keepalive()

        while not RECEIVE_EVENT.is_set():
            r_header = self.sock.recv(BUFF_SIZE)
            r_flag, r_frag_order, r_crc, r_data = menu.initialize_recv_header(r_header)

            if is_FIN(r_flag):
                print(f"FIN, end of connection.")
                print(f" - {count_recv_dgram} fragments were received.")
                self.sock.sendto(create_header_of_fragment(flag_enum.ACK.value, r_frag_order), (CLIENT_IP,CLIENT_PORT))
                break

            if is_END(r_flag):
                print(f"Client quit, I'm (server) quitting too.")
                return

            if is_FILE(r_flag):
                convert_path_to_os = os.path.normpath(r_data.decode('utf-8'))
                is_path = True
                print(f"after convert: {convert_path_to_os}")

            if Validator.is_crc_valid(r_data, r_crc, crc) and is_not_in_dict(r_frag_order, save_frag_message):
                if are_DATA(r_flag):
                    print(f"Received fragment of {r_frag_order} - Size: {len(r_data)} bytes")
                    save_frag_message[r_frag_order] = r_data
                    count_recv_dgram += 1
                    self.sock.sendto(create_header_of_fragment(flag_enum.ACK.value, r_frag_order), (CLIENT_IP,CLIENT_PORT))
            elif Validator.is_crc_valid(r_data, r_crc, crc):
                print(f"Data received, but they are duplicated, fragment {r_frag_order}.")
            else:
                print(f"Fragment {r_frag_order} is damaged. --> NACK")
                print(f" - Received fragment of {r_frag_order} - Size: {len(r_data)} bytes")
                self.sock.sendto(create_header_of_fragment(flag_enum.NACK.value, r_frag_order), (CLIENT_IP,CLIENT_PORT))

        joined_data = b''.join([save_frag_message[frag_order] for frag_order in sorted(save_frag_message.keys())])

        print(f"Total fragments received: {count_recv_dgram}")
        print(f"Final joined data size: {len(joined_data)} bytes")

        # file message
        if is_path:
            save_file(convert_path_to_os, joined_data)
            return

        # text message
        print_text_message(joined_data)


def main():
    global CLIENT_IP
    global CLIENT_PORT
    global SERVER_IP
    global SERVER_PORT
    global SWAP_ROLES
    user_choice = 0

    # SERVER_IP,SERVER_PORT = self.menu.get_ip_input("server/receiver"), self.menu.get_port_input("server/receiver")
    # CLIENT_IP,CLIENT_PORT = self.menu.get_ip_input("client/sender"), self.menu.get_port_input("client/sender")

    while user_choice != 3:

        while user_choice != 3:
            try:
                user_choice = int(input(
                    f"<{color.ORANGE} [1] Client {color.RESET}>\n<{color.ORANGE} [2] Server {color.RESET}>\n___________________\n"))

                if user_choice == 1:
                    client = Client()
                    client.start()
                    client.join()
                elif user_choice == 2:
                    server = Server()
                    server.start()
                    server.join()
                elif user_choice != 3:
                    print(f"{color.RED} ! INVALID CHOICE ! {color.RESET}")

            except ValueError:
                print(f"{color.RED} ! BAD INPUT! Enter a valid integer. {color.RESET}")


main()
