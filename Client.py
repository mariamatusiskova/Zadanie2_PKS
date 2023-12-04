import math
import os
import queue
import random
import socket
import threading
import time
import copy
from queue import Queue

from CRC32 import CRC32
from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator
from ColorPalette import ColorPalette as cp


class Client:
    def __init__(self, menu):
        self.timeout = 5
        self.buff_size = 1465
        self.frag_order = 0
        self.attempts = 3
        self.thread_on = False
        self.menu = copy.deepcopy(menu)
        self.crc = CRC32()
        self.validator = Validator()
        self.receive_thread = None
        self.wait_timeout = 30
        self.server_address = ()
        self.client_address = ()
        self.receive_queue = Queue()
        self.lock_socket = threading.RLock()

    # def keep_alive_client(self, client_socket: socket):
    #     attempts_count = 0
    #     start_time = time.time()
    #
    #     while self.thread_on:
    #
    #         try:
    #             print(f"{cp.BLUE}keep_alive_client:{cp.RESET} im in the loop, thread is on")
    #             print(f"{cp.BLUE}keep_alive_client:{cp.RESET} server address: {self.server_address}")
    #             with self.lock_socket:
    #                 client_socket.sendto(self.initialize_message(FlagEnum.KA.value, 0), self.server_address)
    #             print(f"{cp.BLUE}- Sending KA{cp.RESET}")
    #             r_header = client_socket.recv(self.buff_size)
    #             self.receive_queue.put(r_header)
    #             #r_header = client_socket.recv(self.buff_size)
    #             r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(self.receive_queue_manager(True, FlagEnum.ACK_KA.value))
    #             print(f"{cp.BLUE}keep_alive_client:{cp.RESET} client flag: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")
    #
    #             if self.is_ACK_KA(r_flag):
    #                 print(f"{cp.BLUE}keep_alive_client:{cp.RESET} ACK_KA received.")
    #                 # reset values
    #                 attempts_count = 0
    #                 start_time = time.time()
    #             else:
    #                 print(f"{cp.BLUE}keep_alive_client:{cp.RESET} Error: Didn't receive ACK_KA.")
    #                 attempts_count += 1
    #                 time.sleep(self.wait_timeout)
    #
    #                 if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
    #                     print(f"{cp.BLUE}keep_alive_client:{cp.RESET} Failed to receive ACK_KA after 3 attempts or timeout. Returning to the menu.")
    #                     # Close the socket only if it's still open
    #                     if client_socket.fileno() != -1:
    #                         client_socket.close()
    #                     self.menu.menu()
    #                     self.menu.quit_programme()
    #
    #             time.sleep(self.timeout)
    #
    #         except socket.error as e:
    #             print(f"{cp.RED}Socket error: {e}{cp.RESET}")
    #             # Close the socket in case of an error
    #             if client_socket.fileno() != -1:
    #                 client_socket.close()
    #             break

    def keep_alive_client(self, client_socket: socket):
        attempts_count = 0
        start_time = time.time()

        while self.thread_on:
            try:
                print(f"{cp.BLUE}keep_alive_client:{cp.RESET} im in the loop, thread is on")
                print(f"{cp.BLUE}keep_alive_client:{cp.RESET} server address: {self.server_address}")

                with self.lock_socket:
                    client_socket.sendto(self.initialize_message(FlagEnum.KA.value, 0), self.server_address)
                print(f"{cp.BLUE}- Sending KA{cp.RESET}")

                with self.lock_socket:
                    r_header = client_socket.recv(self.buff_size)
                    self.receive_queue.put(r_header)

                r_message = self.receive_queue_manager(True, FlagEnum.ACK_KA.value)
                r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(r_message)
                print(
                    f"{cp.BLUE}keep_alive_client:{cp.RESET} client flag: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")

                if self.is_ACK_KA(r_flag):
                    print(f"{cp.BLUE}keep_alive_client:{cp.RESET} ACK_KA received.")
                    # reset values
                    attempts_count = 0
                    start_time = time.time()
                else:
                    print(f"{cp.BLUE}keep_alive_client:{cp.RESET} Error: Didn't receive ACK_KA.")
                    attempts_count += 1
                    time.sleep(self.wait_timeout)

                    if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
                        print(
                            f"{cp.BLUE}keep_alive_client:{cp.RESET} Failed to receive ACK_KA after 3 attempts or timeout. Returning to the menu.")
                        # Close the socket only if it's still open
                        if client_socket.fileno() != -1:
                            client_socket.close()
                        self.menu.menu()
                        self.menu.quit_programme()

                time.sleep(self.timeout)

            except socket.error as e:
                print(f"{cp.RED}Socket error: {e}{cp.RESET}")
                # Close the socket in case of an error
                if client_socket.fileno() != -1:
                    client_socket.close()
                break

    def create_thread(self, client_socket: socket):
        self.receive_thread = threading.Thread(target=self.keep_alive_client, args=(client_socket,))
        self.receive_thread.daemon = True
        self.thread_on = True
        self.receive_thread.start()

    # menu for initializing connection
    def handle_client_input(self, client_input: str, client_socket: socket, server_ip: str = "", server_port: int = 0) -> (bool, str, int):
        while True:
            if client_input == 'S':
                server_ip, server_port = self.initialize_client_connection(client_socket, server_ip, server_port)
                print(f"{cp.CYAN}handle_client_input:{cp.RESET} server socket: {client_socket} ########################################")
                return True, server_ip, server_port
            elif client_input == 'RRM':
                print(f"{cp.CYAN}handle_client_input:{cp.RESET} Swapping roles.")
                self.thread_on = False
                self.receive_thread.join()
                client_socket.close()
                # swap
                break
            elif client_input == 'Q':
                self.thread_on = False
                self.receive_thread.join()
                client_socket.close()
                self.menu.quit_programme()
            else:
                print(
                    f"{cp.CYAN}handle_client_input:{cp.RESET} Invalid input. Use 'S' as a settings of the client, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.client_menu()

    def initialize_client_connection(self, client_socket: socket, sent_server_ip: str = "", sent_server_port: int = 0) -> (str, int):
        self.frag_order = 0

        # uncomment for testing purpose
        server_ip, server_port = socket.gethostbyname(socket.gethostname()), 50000

        try:
            # getting details about server
            if sent_server_ip and sent_server_port:
                server_ip, server_port = sent_server_ip, sent_server_port
            #else:
                # server_ip, server_port = self.menu.get_ip_input("server/receiver"), self.menu.get_port_input("server/receiver")

            self.server_address = (server_ip, server_port)
            client_socket.bind(('0.0.0.0', 0))
            own_ip, own_port = client_socket.getsockname()
            print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} own ip: {own_ip} own port: {own_port}")

            self.client_address = (own_ip, own_port)

            if not self.receive_thread:
                print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} Im in if not self.thread_ka:")
                self.create_thread(client_socket)

            # sending initial_header to server
            with self.lock_socket:
                client_socket.sendto(self.initialize_message(FlagEnum.INF.value, self.frag_order), self.server_address)

            with self.lock_socket:
                r_data = client_socket.recv(self.buff_size)
                self.receive_queue.put(r_data)

            # receiving response from the server
            r_data = self.receive_queue_manager(False, FlagEnum.ACK.value)

            # processing received data
            r_flag = self.menu.get_flag(r_data)
            print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} received server flag: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")
            if self.is_ACK(r_flag):
                print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} Connection initialized. Server details: {self.server_address}")
                if client_socket is not None:
                    self.client_sender(client_socket)
                    print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} server socket: {client_socket} ########################################")
                    return server_ip, server_port
            else:
                print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} Connection failed!")
                print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} Message: NACK\n Connection failed!")
        except Exception as e:
            if client_socket:
                client_socket.close()
            print(f"{cp.CYAN}initialize_client_connection:{cp.RESET} An error occurred: {e}. Try again.")

        # Return default values in case of failure
        return server_ip, server_port, client_socket

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

    @staticmethod
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
                print(f"{cp.RED}Didn't find the file. Try again.{cp.RESET}")
            except Exception as e:
                print(f"{cp.RED}An error occurred: {e}. Try again.{cp.RESET}")

    def client_sender(self, client_socket: socket):

        if client_socket is not None:
            while True:
                message_type = self.pick_text_or_file()

                if message_type == 'T':
                    text_message = self.get_text_message_from_input()
                    self.send_message(client_socket, message_type, text_message)
                    break
                elif message_type == 'F':
                    file_message, file_name = self.get_file_message_from_input()
                    self.send_message(client_socket, message_type, file_message, file_name)
                    break
                else:
                    print(f"{cp.RED}Invalid command!{cp.RESET}")
#
    def send_message(self, client_socket: socket, message_type: str, message: bytes, file_name: str = ""):
        self.frag_order = 0

        if client_socket is not None:
            fragment_size = self.get_fragment_size_input()

            if message_type == 'F':
                path_to_save_file = self.get_path_to_save_file(file_name)
                print(f"Sending the file path to the server.")
                with self.lock_socket:
                    client_socket.sendto(self.initialize_message(FlagEnum.FILE.value, self.frag_order, path_to_save_file.encode('utf-8')), self.server_address)

                with self.lock_socket:
                    r_data = client_socket.recv(self.buff_size)
                    self.receive_queue.put(r_data)

                r_data = self.receive_queue_manager(False, FlagEnum.ACK.value)
                r_flag = self.menu.get_flag(r_data)

                if self.is_ACK(r_flag):
                    print(f"Acknowledgment received. Sending the file to the server.")
                else:
                    print(f"{cp.RED}Error: Didn't receive ACK. Unable to complete the operation.{cp.RESET}")
                    return

            dgrams_num = self.count_dgrams(message, fragment_size)
            bad_dgram = self.create_bad_datagram(dgrams_num)

            while self.all_dgrams_send(dgrams_num):
                split_message = message[:fragment_size]
                is_exit = False
                self.frag_order += 1

                attempt_count = 0
                while self.all_attempts(attempt_count):
                    if is_exit:
                        message = message[fragment_size:]
                        break

                    if self.is_bad_dgram(bad_dgram):
                        with self.lock_socket:
                            client_socket.sendto(self.initialize_message(FlagEnum.DATA.value, self.frag_order, split_message) + bytes(101), self.server_address)
                    else:
                        with self.lock_socket:
                            client_socket.sendto(self.initialize_message(FlagEnum.DATA.value, self.frag_order, split_message), self.server_address)

                    print(f" - Sent fragment of {self.frag_order} - Size: {len(split_message)} bytes")

                    try:
                        while True:
                            client_socket.settimeout(self.wait_timeout)

                            with self.lock_socket:
                                r_data = client_socket.recv(self.buff_size)
                                self.receive_queue.put(r_data)

                            r_data = self.receive_queue_manager(False)
                            r_flag = self.menu.get_flag(r_data)
                            r_frag_order = self.menu.get_frag_order(r_data)

                            if self.is_not_valid_dgrams(r_frag_order):
                                print(f"Duplicated, fragment {r_frag_order}.")
                                attempt_count += 1
                                continue

                            if self.is_NACK(r_flag):
                                print(f"NACK: Damaged message.")
                                attempt_count += 1
                                break

                            if self.is_all(dgrams_num):
                                print(f"{self.frag_order} fragments were sent.")
                                with self.lock_socket:
                                    client_socket.sendto(self.initialize_message(FlagEnum.FIN.value, 0), self.server_address)

                            attempt_count = 0
                            is_exit = True
                            break

                    except socket.timeout:
                        print(f"{cp.YELLOW}Timeout! Sending packet again.{cp.RESET}")
                        attempt_count += 1

                if attempt_count == self.attempts:
                    print(f"{cp.RED}Maximum attempts reached. Unable to complete the operation.{cp.RESET}")
                    print(f"Last sent fragment was {self.frag_order} - Size: {len(split_message)} bytes")
                    with self.lock_socket:
                        client_socket.sendto(self.initialize_message(FlagEnum.END.value, 0), self.server_address)
                    break

    def all_attempts(self, attempt_count: int):
        return attempt_count < self.attempts

    def is_bad_dgram(self, bad_dgram_num: int) -> bool:
        return self.frag_order == bad_dgram_num

    @staticmethod
    def is_NACK(r_flag: int) -> bool:
        return r_flag is FlagEnum.NACK.value

    def all_dgrams_send(self, dgrams_num: int) -> bool:
        return self.frag_order < dgrams_num

    def is_all(self, dgrams_num: int) -> bool:
        return self.frag_order == dgrams_num

    def is_not_valid_dgrams(self, r_frag_order: int) -> bool:
        return r_frag_order != self.frag_order

    def initialize_message(self, flag: int, frag_order: int, data: bytes = b'', crc: int = 0) -> bytes:
        if not crc:
            crc = self.crc.calculate(data)
        header = Header(flag, frag_order, crc)
        header_data = header.get_header_body()

        return header_data + data

    def bad_datagram_input(self):
        print(f"Do you want to send a bad fragment during conversation?")
        print('- [Y] yes')
        print('- [N] no')
        answer = self.menu.options()
        answer = answer.upper()

        bool_value = self.validator.is_valid_answer(answer)

        if bool_value is False:
            self.bad_datagram_input()
        return answer

    def create_bad_datagram(self, dgrams_num: int) -> int:
        option = self.bad_datagram_input()

        if option == 'Y':
            return random.randint(1, dgrams_num)
        else:
            return 0

    @staticmethod
    def count_dgrams(message: bytes, fragment_size: int) -> int:
        print(f"len of message: {len(message)}")
        print(f"number of fragments: {int(math.ceil(float(len(message)) / float(fragment_size)))}")
        return int(math.ceil(float(len(message)) / float(fragment_size)))

    def get_fragment_size_input(self) -> int:
        while True:
            try:
                fragment_size = int(input("Enter the size of the fragment, max: <8, 1425>: "))

                if self.validator.is_valid_fragment_size(fragment_size):
                    return fragment_size
                else:
                    print(f"{cp.YELLOW}Invalid input!{cp.RESET}")
            except ValueError:
                print(f"{cp.YELLOW}Invalid input! Please enter a valid integer.{cp.RESET}")

    @staticmethod
    def get_path_to_save_file(file_name: str) -> str:
        while True:
            path = input("Enter the path of the file to send: ")

            if os.path.isdir(path):
                return path + file_name
            else:
                print(f"{cp.YELLOW}Invalid path. Please enter a valid file path.{cp.RESET}")

    @staticmethod
    def get_text_message_from_input() -> bytes:
        return str(input("Enter text message: ")).encode('utf-8')

    @staticmethod
    def is_ACK(r_flag) -> bool:
        return r_flag is FlagEnum.ACK.value

    @staticmethod
    def is_ACK_KA(r_flag) -> bool:
        return r_flag is FlagEnum.ACK_KA.value

    # def send_ACK_KA_back(self, client_socket: socket) -> bytes:
    #     while True:
    #        # r_data = client_socket.recv(self.buff_size)
    #         r_data = client_socket.recv(self.buff_size)
    #         self.receive_queue.put(r_data)
    #
    #         r_flag = self.menu.get_flag(r_data)
    #         print(f"{cp.MAGENTA}send_ACK_KA_back:{cp.RESET} before condition {r_flag}")
    #
    #         if self.is_ACK_KA(r_flag):
    #             print(f"{cp.MAGENTA}send_ACK_KA_back:{cp.RESET} I'm in the condition if self.is_KA {r_flag}")
    #             client_socket.sendto(self.initialize_message(FlagEnum.ACK_KA.value, 0), self.client_address)
    #         else:
    #             return r_data

    def receive_queue_manager(self, ka_flag: bool, flag: int = 3) -> bytes:
        try:
            while True:
                try:
                    r_message = self.receive_queue.get()

                    r_flag = self.menu.get_flag(r_message)

                    if ka_flag and flag == r_flag and FlagEnum.ACK_KA.value == r_flag:
                        return r_message
                    elif not ka_flag and flag == r_flag and FlagEnum.ACK_KA.value != r_flag:
                        return r_message
                    elif not ka_flag and FlagEnum.ACK_KA.value != r_flag:
                        return r_message

                except queue.Empty:
                    print(f"{cp.RED}Queue is empty!{cp.RESET}")
        except Exception as e:
            print(f"{cp.RED}An error occurred in receive_queue_manager: {e}{cp.RESET}")

