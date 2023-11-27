import socket


class Validator:
    def __init__(self):
        pass

    @staticmethod
    def is_valid_ip(ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_port(port):
        try:
            port = int(port)
            return 0 <= port <= 65535
        except ValueError:
            return False

    @staticmethod
    def is_valid_message(message_type: str):
        if message_type == 'F':
            return True
        elif message_type == 'T':
            return True
        else:
            print("Invalid input. Use 'F' as a file or 'M' as a text message.")
            return False

