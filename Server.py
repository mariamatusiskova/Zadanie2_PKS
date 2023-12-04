import copy
import os
import queue
import socket
import threading
import time
from queue import Queue

from CRC32 import CRC32
from FlagEnum import FlagEnum
from Header import Header
from Validator import Validator
from ColorPalette import ColorPalette as cp

# SERVER_IP = "0.0.0.0"
SERVER_IP = "localhost"
SERVER_HOST_IP = socket.gethostbyname(socket.gethostname())


class Server:
    def __init__(self, menu):
        self.count_recv_dgram = 0
        self.buff_size = 1465
        self.menu = copy.deepcopy(menu)
        self.crc = CRC32()
        self.validator = Validator()
        self.wait_timeout = 30
        self.receive_thread = None
        self.thread_on = False
        self.attempts = 3
        self.timeout = 5
        self.server_address = ()
        self.client_address = ()
        self.receive_queue = Queue()
        self.lock_socket = threading.RLock()

    # def keep_alive_server(self, server_socket: socket, server_address: tuple):
    #     attempts_count = 0
    #     start_time = time.time()
    #
    #     while self.thread_on:
    #         print(f"{cp.PINK}keep_alive_server:{cp.RESET} im in the loop, thread is on")
    #
    #         try:
    #             r_header, self.client_address = server_socket.recvfrom(self.buff_size)
    #             self.receive_queue.put(r_header)
    #
    #             r_header = self.receive_queue_manager(True, FlagEnum.KA.value)
    #
    #             r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(r_header)
    #             print(f"{cp.PINK}keep_alive_server:{cp.RESET} server KA: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")
    #             if self.is_KA(r_flag):
    #                 # reset values
    #                 attempts_count = 0
    #                 start_time = time.time()
    #
    #                 with self.lock_socket:
    #                     server_socket.sendto(self.initialize_message(FlagEnum.ACK_KA.value, r_frag_order), self.client_address)
    #             else:
    #                 with self.lock_socket:
    #                     server_socket.sendto(self.initialize_message(r_flag, r_frag_order, r_data, r_crc), server_address)
    #                 print(f"{cp.PINK}keep_alive_server:{cp.RESET} Error: Didn't receive KA.")
    #                 attempts_count += 1
    #                 time.sleep(self.wait_timeout)
    #
    #                 if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
    #                     print(f"{cp.RED}Failed to receive KA after 3 attempts or timeout. Returning to the menu.{cp.RESET}")
    #                     # Close the socket only if it's still open
    #                     if server_socket.fileno() != -1:
    #                         server_socket.close()
    #                     self.menu.menu()
    #                     break
    #         except socket.error as e:
    #             print(f"{cp.RED}Socket error: {e}{cp.RESET}")
    #             # Close the socket in case of an error
    #             if server_socket.fileno() != -1:
    #                 server_socket.close()
    #             break

    def keep_alive_server(self, server_socket: socket, server_address: tuple):
        attempts_count = 0
        start_time = time.time()

        while self.thread_on:
            print(f"{cp.PINK}keep_alive_server:{cp.RESET} im in the loop, thread is on")

            try:
                r_header, self.client_address = server_socket.recvfrom(self.buff_size)
                self.receive_queue.put(r_header)

                r_header = self.receive_queue_manager(True, FlagEnum.KA.value)

                r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(r_header)
                print(
                    f"{cp.PINK}keep_alive_server:{cp.RESET} server KA: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")

                if self.is_KA(r_flag):
                    # reset values
                    attempts_count = 0
                    start_time = time.time()
                    server_socket.sendto(self.initialize_message(FlagEnum.ACK_KA.value, r_frag_order),
                                         self.client_address)
                else:
                    server_socket.sendto(self.initialize_message(r_flag, r_frag_order, r_data, r_crc), server_address)
                    print(f"{cp.PINK}keep_alive_server:{cp.RESET} Error: Didn't receive KA.")
                    attempts_count += 1
                    time.sleep(self.wait_timeout)

                    if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
                        print(
                            f"{cp.RED}Failed to receive KA after 3 attempts or timeout. Returning to the menu.{cp.RESET}")
                        # Close the socket only if it's still open
                        if server_socket.fileno() != -1:
                            server_socket.close()
                        self.menu.menu()
                        break
            except socket.error as e:
                print(f"{cp.RED}Socket error: {e}{cp.RESET}")
                # Close the socket in case of an error
                if server_socket.fileno() != -1:
                    server_socket.close()
                break

    def create_thread(self, server_socket: socket):
        self.receive_thread = threading.Thread(target=self.keep_alive_server, args=(server_socket, self.server_address))
        self.receive_thread.daemon = True
        self.thread_on = True
        self.receive_thread.start()

    def handle_server_input(self, server_input: str, server_socket: socket, server_port: int = 0) -> (bool, int):
        while True:
            if server_input == 'S':
                server_port = self.initialize_server_connection(server_socket, server_port)
                print(f"{cp.MAGENTA}server socket:{cp.RESET} {server_socket} ########################################")
                return True, server_port
            elif server_input == 'RRM':
                print(f"Swapping roles.")
                self.thread_on = False
                self.receive_thread.join()
                server_socket.close()
                # swap
                break
            elif server_input == 'Q':
                self.thread_on = False
                self.receive_thread.join()
                server_socket.close()
                self.menu.quit_programme()
            else:
                print(f"{cp.YELLOW}Invalid input. Use 'S' as a settings of the server, 'RRM' as a role reversal message or 'Q' as quit.{cp.RESET}")
                self.menu.server_menu()

    # def initialize_server_connection(self, server_socket: socket, sent_server_port: int = 0) -> int:
    #
    #     # uncomment for testing purpose
    #     server_port = 50000
    #
    #     try:
    #         # getting details about server and receiver
    #         if sent_server_port:
    #             server_port = sent_server_port
    #         #else:
    #             # server_port = self.menu.get_port_input("receiver")
    #         server_details = (SERVER_HOST_IP, server_port)
    #
    #         with server_socket:
    #             server_socket.bind(server_details)
    #             self.server_address = server_details
    #
    #         if not self.receive_thread:
    #             print(f"initialize_server_connection: Im in if not self.thread_ka:")
    #             self.create_thread(server_socket)
    #
    #         # receiving response from the client
    #         r_header = server_socket.recv(self.buff_size)
    #         self.receive_queue.put(r_header)
    #
    #         r_data = self.receive_queue_manager(False, FlagEnum.INF.value)
    #         print(f"data: {r_data}")
    #
    #         # sending initial_header to client
    #         server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, 0), self.client_address)
    #
    #         # processing received data
    #         r_flag = self.menu.get_flag(r_data)
    #
    #         if self.is_INF(r_flag):
    #             print(f"Connection initialized. Client details: {self.client_address}")
    #             if server_socket is not None:
    #                 self.server_sender(server_socket)
    #                 print(f"{cp.MAGENTA}server socket:{cp.RESET} {server_socket} ########################################")
    #                 return server_port
    #         else:
    #             print(f"{cp.RED}Connection failed!{cp.RESET}")
    #     except Exception as e:
    #         if server_socket:
    #             server_socket.close()
    #         print(f"{cp.RED}initialize_server_connection: An error occurred: {e}. Try again.{cp.RESET}")

    # def initialize_server_connection(self, server_socket: socket, sent_server_port: int = 0) -> int:
    #     server_port = sent_server_port or 50000  # Set a default value if not provided
    #
    #     try:
    #         server_details = (SERVER_HOST_IP, server_port)
    #
    #         with server_socket:
    #             server_socket.bind(server_details)
    #             self.server_address = server_details
    #
    #             if not self.receive_thread:
    #                 print(f"initialize_server_connection: Im in if not self.thread_ka:")
    #                 self.create_thread(server_socket)
    #
    #             # receiving response from the client
    #             r_header = server_socket.recv(self.buff_size)
    #             self.receive_queue.put(r_header)
    #
    #             r_data = self.receive_queue_manager(False, FlagEnum.INF.value)
    #             print(f"data: {r_data}")
    #
    #             # sending initial_header to client
    #             with self.lock_socket:
    #                 server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, 0), self.client_address)
    #
    #             # processing received data
    #             r_flag = self.menu.get_flag(r_data)
    #
    #             if self.is_INF(r_flag):
    #                 print(f"Connection initialized. Client details: {self.client_address}")
    #                 if server_socket is not None:
    #                     self.server_sender(server_socket)
    #                     print(
    #                         f"{cp.MAGENTA}server socket:{cp.RESET} {server_socket} ########################################")
    #                     return server_port
    #             else:
    #                 print(f"{cp.RED}Connection failed!{cp.RESET}")
    #     except Exception as e:
    #         print(f"{cp.RED}initialize_server_connection: An error occurred: {e}. Try again.{cp.RESET}")

    def initialize_server_connection(self, server_socket: socket, sent_server_port: int = 0) -> int:
        server_port = sent_server_port or 50000  # Set a default value if not provided

        try:
            server_details = (SERVER_HOST_IP, server_port)

            with server_socket:
                server_socket.bind(server_details)
                self.server_address = server_details

                if not self.receive_thread:
                    print(f"initialize_server_connection: Im in if not self.thread_ka:")
                    self.create_thread(server_socket)

                # receiving response from the client
                r_header = server_socket.recv(self.buff_size)
                self.receive_queue.put(r_header)

                r_data = self.receive_queue_manager(False, FlagEnum.INF.value)
                print(f"data: {r_data}")

                # sending initial_header to client
                server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, 0), self.client_address)

                # processing received data
                r_flag = self.menu.get_flag(r_data)

                if self.is_INF(r_flag):
                    print(f"Connection initialized. Client details: {self.client_address}")
                    if server_socket is not None:
                        self.server_sender(server_socket)
                        print(
                            f"{cp.MAGENTA}server socket:{cp.RESET} {server_socket} ########################################")
                        return server_port
                else:
                    print(f"{cp.RED}Connection failed!{cp.RESET}")
        except Exception as e:
            print(f"{cp.RED}initialize_server_connection: An error occurred: {e}. Try again.{cp.RESET}")

    def initialize_message(self, flag: int, frag_order: int, data: bytes = b'', crc: int = 0) -> bytes:
        if not crc:
            crc = self.crc.calculate(data)

        header = Header(flag, frag_order, crc)
        header_data = header.get_header_body()

        return header_data + data

    def server_sender(self, server_socket: socket):
        self.count_recv_dgram = 0
        save_frag_message = {}
        is_path = False
        convert_path_to_os = ""

        if server_socket is not None:
            while True:

                r_header = server_socket.recv(self.buff_size)
                self.receive_queue.put(r_header)

                r_header = self.receive_queue_manager(False)
                r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(r_header)

                if self.is_FIN(r_flag):
                    print(f"FIN, end of connection.")
                    print(f" - {self.count_recv_dgram} fragments were received.")
                    server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, r_frag_order), self.client_address)
                    break

                if self.is_END(r_flag):
                    print(f"Client quit, I'm (server) quitting too.")
                    return

                if self.is_FILE(r_flag):
                    convert_path_to_os = os.path.normpath(r_data.decode('utf-8'))
                    is_path = True
                    print(f"after convert: {convert_path_to_os}")

                if self.validator.is_crc_valid(r_data, r_crc, self.crc) and self.is_not_in_dict(r_frag_order, save_frag_message):
                    if self.is_DATA(r_flag):
                        print(f"Received fragment of {r_frag_order} - Size: {len(r_data)} bytes")
                        save_frag_message[r_frag_order] = r_data
                        self.count_recv_dgram += 1
                        server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, r_frag_order), self.client_address)
                elif self.validator.is_crc_valid(r_data, r_crc, self.crc):
                    print(f"Data received, but they are duplicated, fragment {r_frag_order}.")
                else:
                    print(f"Fragment {r_frag_order} is damaged. --> NACK")
                    print(f" - Received fragment of {r_frag_order} - Size: {len(r_data)} bytes")
                    server_socket.sendto(self.initialize_message(FlagEnum.NACK.value, r_frag_order), self.client_address)

            joined_data = b''.join([save_frag_message[frag_order] for frag_order in sorted(save_frag_message.keys())])

            print(f"Total fragments received: {self.count_recv_dgram}")
            print(f"Final joined data size: {len(joined_data)} bytes")

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
            print(f"{cp.RED}Unable to decode data as UTF-8. This may not be a text file.{cp.RESET}")

    @staticmethod
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
            print(f"{cp.RED}Error saving file: {e} {cp.RESET}")

    @staticmethod
    def is_not_in_dict(r_frag_order: int, save_frag_message: dict) -> bool:
        return r_frag_order not in save_frag_message

    @staticmethod
    def is_FIN(r_flag) -> bool:
        return r_flag is FlagEnum.FIN.value

    @staticmethod
    def is_INF(r_flag) -> bool:
        return r_flag is FlagEnum.INF.value

    @staticmethod
    def is_FILE(r_flag) -> bool:
        return r_flag is FlagEnum.FILE.value

    @staticmethod
    def is_END(r_flag) -> bool:
        return r_flag is FlagEnum.END.value

    @staticmethod
    def is_KA(r_flag) -> bool:
        return r_flag is FlagEnum.KA.value

    @staticmethod
    def is_DATA(r_flag) -> bool:
        return r_flag is FlagEnum.DATA.value

    # def receive_queue_manager(self, ka_flag: bool, flag: int = 7) -> bytes:
    #     try:
    #         while True:
    #             try:
    #                 r_message = self.receive_queue.get()
    #
    #                 r_flag = self.menu.get_flag(r_message)
    #
    #                 if ka_flag and flag == r_flag:
    #                     return r_message
    #                 elif flag == r_flag:
    #                     return r_message
    #                 else:
    #                     return r_message
    #
    #             except queue.Empty:
    #                 print(f"{cp.RED}Queue is empty!{cp.RESET}")
    #     except Exception as e:
    #         print(f"{cp.RED}An error occurred in receive_queue_manager: {e}{cp.RESET}")

    def receive_queue_manager(self, ka_flag: bool, flag: int = 7) -> bytes:
        try:
            while self.thread_on:
                try:
                    r_message = self.receive_queue.get(timeout=1)  # Add a timeout to avoid high CPU usage
                    r_flag = self.menu.get_flag(r_message)

                    if ka_flag and flag == r_flag and FlagEnum.KA.value == r_flag:
                        return r_message
                    elif not ka_flag and flag == r_flag and FlagEnum.KA.value != r_flag:
                        return r_message
                    elif not ka_flag and FlagEnum.KA.value != r_flag:
                        return r_message

                    self.receive_queue.put(r_message)
                    break

                    print(f"{cp.ORANGE}receive_queue_manager: Didn't return{cp.RESET}")

                except queue.Empty:
                    pass  # Continue the loop if the queue is empty
        except Exception as e:
            print(f"{cp.RED}An error occurred in receive_queue_manager: {e}{cp.RESET}")
