import math
import os
import random
import socket
import threading
import time

from CRC32 import CRC32
from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator


class Client:
    def __init__(self, menu):
        self.timeout = 5
        self.buff_size = 1465
        self.frag_order = 0
        self.attempts = 3
        self.thread_on = False
        self.menu = menu
        self.crc = CRC32()
        self.validator = Validator()
        self.thread_ka = None
        self.wait_timeout = 15

    def keep_alive(self, client_socket: socket, server_details: tuple):
        attempts_count = 0
        start_time = time.time()

        try:
            while self.thread_on:
                client_socket.sendto(self.initialize_message(FlagEnum.KA.value, 0), server_details)
                r_data = client_socket.recv(self.buff_size)
                r_flag = self.menu.get_flag(r_data)

                if self.is_ACK(r_flag):
                    print("Keep-alive client: Acknowledgment received.")
                    # reset values
                    attempts_count = 0
                    start_time = time.time()
                else:
                    print("Client keep-alive: Error: Didn't receive ACK.")
                    attempts_count += 1
                    time.sleep(self.wait_timeout)

                    if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
                        print("Failed to receive ACK after 3 attempts or timeout. Returning to the menu.")
                        # Close the socket only if it's still open
                        if client_socket.fileno() != -1:
                            client_socket.close()
                        self.menu.menu()
                        self.menu.quit_programme()

                time.sleep(self.timeout)
        finally:
            client_socket.close()

    def create_thread(self, client_socket: socket, server_details: tuple) -> threading:
        self.thread_ka = threading.Thread(target=self.keep_alive, args=(client_socket, server_details))
        self.thread_ka.daemon = True
        self.thread_on = True
        self.thread_ka.start()

    # menu for initializing connection
    def handle_client_input(self, client_input: str, client_socket: socket, server_ip: str = "", server_port: int = 0) -> (bool, str, int):
        while True:
            if client_input == 'S':
                server_ip, server_port = self.initialize_client_connection(client_socket, server_ip, server_port)
                print(f"server socket: {client_socket} ########################################")
                return True, server_ip, server_port
            elif client_input == 'RRM':
                print("Swapping roles.")
                self.thread_on = False
                self.thread_ka.join()
                client_socket.close()
                # swap
                break
            elif client_input == 'Q':
                self.thread_on = False
                self.thread_ka.join()
                client_socket.close()
                self.menu.quit_programme()
            else:
                print(
                    "Invalid input. Use 'S' as a settings of the client, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.client_menu()

    def initialize_client_connection(self, client_socket: socket, sent_server_ip: str = "", sent_server_port: int = 0) -> (str, int):
        self.frag_order = 0

        # uncomment for testing purpose
        server_ip, server_port = "localhost", 50000

        try:
            # getting details about server
            if sent_server_ip and sent_server_port:
                server_ip, server_port = sent_server_ip, sent_server_port
            #else:
                # server_ip, server_port = self.menu.get_ip_input("server/receiver"), self.menu.get_port_input("server/receiver")

            server_details = (server_ip, server_port)

            # sending initial_header to server
            client_socket.sendto(self.initialize_message(FlagEnum.INF.value, self.frag_order), server_details)
            if not self.thread_ka:
                self.create_thread(client_socket, server_details)

            # receiving response from the server
            received_flag, server_address = client_socket.recvfrom(self.buff_size)

            # processing received data
            r_flag = self.menu.get_flag(received_flag)
            if self.is_ACK(r_flag):
                print(f"Connection initialized. Server details: {server_address}")
                if client_socket is not None:
                    self.client_sender(client_socket, server_address)
                    print(f"server socket: {client_socket} ########################################")
                    return server_ip, server_port
            else:
                print("Connection failed!")
                print("Message: NACK\n Connection failed!")
        except Exception as e:
            if client_socket:
                client_socket.close()
            print(f"initialize_client_connection: An error occurred: {e}. Try again.")

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
                    break
                elif message_type == 'F':
                    file_message, file_name = self.get_file_message_from_input()
                    self.send_message(client_socket, server_address, message_type, file_message, file_name)
                    break
                else:
                    print("Invalid command!")

    def send_message(self, client_socket: socket, server_address: tuple, message_type: str, message: bytes, file_name: str = ""):
        self.frag_order = 0

        if client_socket is not None:
            fragment_size = self.get_fragment_size_input()

            if message_type == 'F':
                path_to_save_file = self.get_path_to_save_file(file_name)
                print("Sending the file path to the server.")
                client_socket.sendto(self.initialize_message(FlagEnum.FILE.value, self.frag_order, path_to_save_file.encode('utf-8')), server_address)
                r_data = client_socket.recv(self.buff_size)
                r_flag = self.menu.get_flag(r_data)

                if self.is_ACK(r_flag):
                    print("Acknowledgment received. Sending the file to the server.")
                else:
                    print("Error: Didn't receive ACK. Unable to complete the operation.")
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
                        client_socket.sendto(self.initialize_message(FlagEnum.DATA.value, self.frag_order, split_message) + bytes(101), server_address)
                    else:
                        client_socket.sendto(self.initialize_message(FlagEnum.DATA.value, self.frag_order, split_message), server_address)

                    print(f" - Sent fragment of {self.frag_order} - Size: {len(split_message)} bytes")

                    try:
                        while True:
                            client_socket.settimeout(self.wait_timeout)

                            r_data = client_socket.recv(self.buff_size)
                            r_flag = self.menu.get_flag(r_data)
                            r_frag_order = self.menu.get_frag_order(r_data)

                            if self.is_not_valid_dgrams(r_frag_order):
                                print(f"Duplicated, fragment {r_frag_order}.")
                                attempt_count += 1
                                continue

                            if self.is_NACK(r_flag):
                                print("NACK: Damaged message.")
                                attempt_count += 1
                                break

                            if self.is_all(dgrams_num):
                                print(f"{self.frag_order} fragments were sent.")
                                client_socket.sendto(self.initialize_message(FlagEnum.FIN.value, 0), server_address)

                            attempt_count = 0
                            is_exit = True
                            break

                    except socket.timeout:
                        print("Timeout! Sending packet again.")
                        attempt_count += 1

                if attempt_count == self.attempts:
                    print("Maximum attempts reached. Unable to complete the operation.")
                    print(f"Last sent fragment was {self.frag_order} - Size: {len(split_message)} bytes")
                    client_socket.sendto(self.initialize_message(FlagEnum.END.value, 0), server_address)
                    break

    def all_attempts(self, attempt_count: int):
        return attempt_count < self.attempts

    def is_bad_dgram(self, bad_dgram) -> bool:
        return bad_dgram == self.frag_order
    @staticmethod
    def is_NACK(r_flag: int) -> bool:
        return r_flag is FlagEnum.NACK.value

    def all_dgrams_send(self, dgrams_num: int) -> bool:
        return self.frag_order < dgrams_num

    def is_all(self, dgrams_num: int) -> bool:
        return self.frag_order == dgrams_num

    def is_not_valid_dgrams(self, r_frag_order: int) -> bool:
        return r_frag_order != self.frag_order

    def initialize_message(self, flag: int, frag_order: int, data: bytes = b'') -> bytes:
        header = Header(flag, frag_order, self.crc.calculate(data))
        header_data = header.get_header_body()

        return header_data + data

    def is_bad_dgram(self, bad_dgram_num: int) -> bool:
        return self.frag_order == bad_dgram_num

    def bad_datagram_input(self):
        print("Do you want to send a bad fragment during conversation?")
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
                    print("Invalid input!")
            except ValueError:
                print("Invalid input! Please enter a valid integer.")

    @staticmethod
    def get_path_to_save_file(file_name: str) -> str:
        while True:
            path = input("Enter the path of the file to send: ")

            if os.path.isdir(path):
                return path + file_name
            else:
                print("Invalid path. Please enter a valid file path.")

    @staticmethod
    def get_text_message_from_input() -> bytes:
        return str(input("Enter text message: ")).encode('utf-8')

    @staticmethod
    def is_ACK(r_flag) -> bool:
        return r_flag is FlagEnum.ACK.value
