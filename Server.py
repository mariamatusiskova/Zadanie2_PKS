import os
import socket
import threading
import time

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
        self.wait_timeout = 30
        self.thread_ka = None
        self.thread_on = False
        self.attempts = 3
        self.timeout = 5
        self.server_address = ()
        self.client_address = ()

    def keep_KA_sending(self, server_socket: socket, server_address: tuple):
        attempts_count = 0
        start_time = time.time()

        while self.thread_on:
            print("keep_KA_sending: im in the loop, thread is on")
            r_header, self.client_address = server_socket.recvfrom(self.buff_size)
            r_flag, r_frag_order, r_crc, r_data = self.menu.initialize_recv_header(r_header)
            print(f"keep_KA_sending: server KA: {r_flag} (((((((((((((((((((((((((((((((((((((((((((")
            if self.is_KA(r_flag):
                # reset values
                attempts_count = 0
                start_time = time.time()
                server_socket.sendto(self.initialize_message(FlagEnum.ACK_KA.value, r_frag_order), self.client_address)
            else:
                server_socket.sendto(self.initialize_message(r_flag, r_frag_order, r_data, r_crc), server_address)
                print("server keep-alive server: Error: Didn't receive KA.")
                attempts_count += 1
                time.sleep(self.wait_timeout)

                if attempts_count >= self.attempts or time.time() - start_time >= self.wait_timeout:
                    print("Failed to receive KA after 3 attempts or timeout. Returning to the menu.")
                    # Close the socket only if it's still open
                    if server_socket.fileno() != -1:
                        server_socket.close()
                    self.menu.menu()
                    break

    def create_thread(self, server_socket: socket):
        self.thread_ka = threading.Thread(target=self.keep_KA_sending, args=(server_socket, self.server_address))
        self.thread_ka.daemon = True
        self.thread_on = True
        self.thread_ka.start()

    def handle_server_input(self, server_input: str, server_socket: socket, server_port: int = 0) -> (bool, int):
        while True:
            if server_input == 'S':
                server_port = self.initialize_server_connection(server_socket, server_port)
                print(f"server socket: {server_socket} ########################################")
                return True, server_port
            elif server_input == 'RRM':
                print("Swapping roles.")
                self.thread_on = False
                self.thread_ka.join()
                server_socket.close()
                # swap
                break
            elif server_input == 'Q':
                self.thread_on = False
                self.thread_ka.join()
                server_socket.close()
                self.menu.quit_programme()
            else:
                print("Invalid input. Use 'S' as a settings of the server, 'RRM' as a role reversal message or 'Q' as quit.")
                self.menu.server_menu()

    def initialize_server_connection(self, server_socket: socket, sent_server_port: int = 0) -> int:

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
            self.server_address = server_details

            if not self.thread_ka:
                print("initialize_server_connection: Im in if not self.thread_ka:")
                self.create_thread(server_socket)

            # receiving response from the client
            r_data = self.send_KA_back(server_socket)
            print(f"data: {r_data}")

            # sending initial_header to client
            server_socket.sendto(self.initialize_message(FlagEnum.ACK.value, 0), self.client_address)

            # processing received data
            r_flag = self.menu.get_flag(r_data)

            if self.is_INF(r_flag):
                print(f"Connection initialized. Client details: {self.client_address}")
                if server_socket is not None:
                    self.server_sender(server_socket)
                    print(f"server socket: {server_socket} ########################################")
                    return server_port
            else:
                print("Connection failed!")
        except Exception as e:
            if server_socket:
                server_socket.close()
            print(f"initialize_server_connection: An error occurred: {e}. Try again.")

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
                r_header = self.send_KA_back(server_socket)
                r_flag, r_frag_order, r_crc, r_data = self.initialize_recv_header(r_header)

                if self.is_FIN(r_flag):
                    print("FIN, end of connection.")
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
            print("Unable to decode data as UTF-8. This may not be a text file.")

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
            print(f"Error saving file: {e}")

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

    def send_KA_back(self, server_socket: socket) -> bytes:
        while True:
            r_data = server_socket.recv(self.buff_size)
            r_flag = self.menu.get_flag(r_data)
            print(f"send_ACK_KA_back: before condition {r_flag}")

            if self.is_KA(r_flag):
                print(f"send_KA_back: I'm in the condition if self.is_KA {r_flag}")
                server_socket.sendto(self.initialize_message(FlagEnum.KA.value, 0), self.server_address)
            else:
                return r_data
