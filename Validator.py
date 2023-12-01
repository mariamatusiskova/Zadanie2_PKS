import socket


class Validator:
    def __init__(self):
        pass

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_port(port: str) -> bool:
        try:
            port = int(port)
            return 0 <= port <= 65535
        except ValueError:
            return False

    @staticmethod
    def is_valid_message(message_type: str) -> bool:
        if message_type == 'F':
            return True
        elif message_type == 'T':
            return True
        else:
            print("Invalid input. Use 'F' as a file or 'M' as a text message.")
            return False

    @staticmethod
    def is_valid_answer(answer: str) -> bool:
        if answer == 'Y':
            return True
        elif answer == 'N':
            return True
        else:
            print("Invalid input. Use 'Y' as yes or 'N' as a no.")
            return False

    @staticmethod
    def is_valid_fragment_size(fragment_size: int) -> bool:
        if fragment_size < 6:
            return False
        elif fragment_size > 1425:
            return False
        else:
            return True


