import os
import socket
import struct
import threading
import binascii
import time

# Konštanta pre veľkosť hlavičky (8 bajtov pre poradové číslo fragmentu a veľkosť fragmentu)
HEADER_SIZE = 9
max_fragment_size = 256


class Client:
    def __init__(self, server_ip, server_port) -> None:
        self.kon = False
        self.spojenie = False
        self.server = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_ip = server_ip
        self.server_port = server_port

    def switcher(self):
        t3 = threading.Thread(target=self.ka, args=())
        if self.kon:
            self.kon = False
            t3.start()
        vstup = input("Zadajte operaciu: ")
        global max_fragment_size
        if vstup == "K":
            if self.spojenie:
                self.kon = True
                t3.join()
            self.ukoncenie_spojenia()
        elif vstup == "P":
            self.nadviazanie_spojenia()
        elif vstup == "S":
            self.kon = True
            max_fragment_size = int(input("Zadajte maximalnu velkost fragmentu: "))
            while 1449 <= max_fragment_size or max_fragment_size <= 51:
                max_fragment_size = int(input("Zadajte maximalnu velkost fragmentu: "))
            t3.join()
            self.sock.settimeout(None)
            self.sock.sendto(bytes("0" + str(max_fragment_size), encoding="utf8"), (self.server_ip, self.server_port))
            self.receive_file(input("Zadajte cestu kam ma byt subor ulozeny, pri kazdom lomizku zadajte este jedno:"), input("Zadajte cestu k suboru, pri kazdom lomizku zadajte este jedno:"))
        elif vstup == "T":
            self.kon = True
            max_fragment_size = int(input("Zadajte maximalnu velkost fragmentu: "))
            while 1449 <= max_fragment_size or max_fragment_size <= 51:
                max_fragment_size = int(input("Zadajte maximalnu velkost fragmentu: "))
            t3.join()
            self.sock.settimeout(None)
            self.sock.sendto(bytes("0" + str(max_fragment_size), encoding="utf8"), (self.server_ip, self.server_port))
            typ = input("S pre poslanie a R pre prijatie spravy: ")
            if typ == "R":
                self.sock.sendto(b"34", (self.server_ip, self.server_port))
                self.receive_text()
            else:
                self.sock.sendto(b"24", (self.server_ip, self.server_port))
                self.send_text()
        elif vstup == "V":
            self.kon = True
            t3.join()
            self.sock.sendto(b"7", (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(128)
            if data == b"10":
                port = self.sock.getsockname()[1]
                self.sock.close()
                #s = Server(socket.gethostbyname(socket.gethostname()), port)
                s = Server(socket.gethostbyname(socket.gethostname()), self.server_port)
                s.switcher()
        else:
            self.kon = True
            t3.join()
            self.switcher()

    def ka(self):
        while not self.kon:
            self.sock.settimeout(5)
            try:
                data, self.server = self.sock.recvfrom(128)
            except socket.timeout:
                self.sock.sendto(b"6", (self.server_ip, self.server_port))
                data, self.server = self.sock.recvfrom(128)
                if data == b"10":
                    continue
                else:
                    self.kon = True
                    self.ukoncenie_spojenia()
                    print("Spojenie ukoncene z dovodu neodpovedania servera")

    def nadviazanie_spojenia(self):
        self.kon = True
        self.sock.sendto(b"1", (self.server_ip, self.server_port))  # SYN
        data, self.server = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
        if data == b"11":  # ACK,SYN
            self.sock.sendto(b"10", (self.server_ip, self.server_port))  # ACK
            print("Klient: Spojenie nadviazane")
            self.spojenie = True
        else:
            print("Klient: Spojenie nenadviazane")
        data, self.server = self.sock.recvfrom(128)
        if data == b"1":
            self.sock.sendto(b"7", (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(128)
            if data == b"10":
                port = self.sock.getsockname()[1]
                self.sock.close()
                # s = Server(socket.gethostbyname(socket.gethostname()), port)
                s = Server(socket.gethostbyname(socket.gethostname()), self.server_port)
                s.switcher()
        else:
            self.switcher()

    def ukoncenie_spojenia(self):
        if self.spojenie:
            self.sock.sendto(b"2", (self.server_ip, self.server_port))  # FYN
            data1, self.server = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
            if data1 == b"12":  # ACK,FYN
                self.sock.sendto(b"10", (self.server_ip, self.server_port))
                self.sock.close()
                print("Klient: Spojenie ukoncene")
                return 1
            else:
                print("Klient: Spojenie neukoncene")
        else:
            self.sock.close()
            print("Klient: Spojenie ukoncene")

    def receive_file(self, save_path, file_path):
        self.sock.sendto(b"3", (self.server_ip, self.server_port))
        data, self.server = self.sock.recvfrom(128)
        if data == b"13":
            print("Server prijal poziadavku na prenos suboru")
            self.sock.sendto(b"10", (self.server_ip, self.server_port))
            self.sock.sendto(bytes(file_path, encoding="utf8"), (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
            if data == b"10":
                print("Server prijal adresu suboru")
                meno = ""
                x = len(file_path) - 1
                while file_path[x] != "\\":
                    meno = file_path[x] + meno
                    x -= 1
                # Otvorenie súboru na zápis
                with open(save_path + meno, 'wb') as file:
                    print("Otvorenie suboru na zapis s nazvom: ", meno, "a cestou: ", save_path + meno, "\n")
                    expected_sequence_number = 0
                    while True:
                        # Prijatie fragmentu
                        data, self.server = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
                        # Overenie poradového čísla
                        flag, crc, sequence_number = struct.unpack('!BII', data[:HEADER_SIZE])
                        c = binascii.crc_hqx(data[HEADER_SIZE:], 0)
                        if sequence_number == expected_sequence_number and flag == 5 and crc == c:
                            # Zapísanie dát do súboru
                            file.write(data[HEADER_SIZE:])  # neviem preco 4
                            expected_sequence_number += 1
                            print(expected_sequence_number, "fragment bol prijaty s velkostou", len(data)+42)
                            # Poslanie potvrdenia o prijatí fragmentu
                            self.sock.sendto(b"10", self.server)
                        else:
                            # Odozva na chybný fragment
                            # self.sock.sendto(struct.pack('!I', expected_sequence_number), self.server)
                            print("paket s cislom", sequence_number, "nebol prijaty, pozadovy bol",
                                  expected_sequence_number + 1)
                            self.sock.sendto(bytes("0" + str(expected_sequence_number), encoding="utf8"), self.server)

                        # Koniec prenosu
                        if len(data)-9 < max_fragment_size-51:
                            break

                print("Súbor s velkostou", os.path.getsize(save_path + meno), "úspešne prijatý")
                print("Bol ulozeny na adrese:", save_path + meno,
                      "\n################Koniec prenosu################\n\n")
        data, self.server = self.sock.recvfrom(128)
        if data == b"1":
            self.sock.sendto(b"7", (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(128)
            if data == b"10":
                port = self.sock.getsockname()[1]
                self.sock.close()
                # s = Server(socket.gethostbyname(socket.gethostname()), port)
                s = Server(socket.gethostbyname(socket.gethostname()), self.server_port)
                s.switcher()
        else:
            self.switcher()

    def receive_text(self):
        data, self.server = self.sock.recvfrom(128)
        if data == b"14":
            print("Server prijal poziadavku na prenos dat")
            velkost, self.server = self.sock.recvfrom(128)
            vel = int(str(velkost)[2:len(str(velkost)) - 1])
            expected_sequence_number = 0
            text = ""
            while True:
                # Prijatie fragmentu
                data, self.server = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
                # Overenie poradového čísla
                flag, crc, sequence_number = struct.unpack('!BII', data[:HEADER_SIZE])
                if len(text) < vel:
                    if sequence_number == expected_sequence_number and flag == 4 and crc == binascii.crc_hqx(
                            data[HEADER_SIZE:], 0):
                        # Zapísanie dát do súboru
                        text += str(data[HEADER_SIZE:])[2:len(str(data[HEADER_SIZE:])) - 1]
                        expected_sequence_number += 1
                        print(expected_sequence_number, "fragment bol prijaty s velkostou", len(data)+42)
                        # Poslanie potvrdenia o prijatí fragmentu
                        self.sock.sendto(struct.pack('!I', sequence_number), self.server)
                    else:
                        # Odozva na chybný fragment
                        self.sock.sendto(struct.pack('!I', expected_sequence_number), self.server)

                # Koniec prenosu
                if len(data) - 9 < max_fragment_size - 51:
                    break

            print("Sprava zo serveru: ", text)
        data, self.server = self.sock.recvfrom(128)
        if data == b"1":
            self.sock.sendto(b"7", (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(128)
            if data == b"10":
                port = self.sock.getsockname()[1]
                self.sock.close()
                # s = Server(socket.gethostbyname(socket.gethostname()), port)
                s = Server(socket.gethostbyname(socket.gethostname()), self.server_port)
                s.switcher()
        else:
            self.switcher()

    def send_text(self):
        self.sock.sendto(b"14", self.server)
        text = "AHOJ JA SOM CLIENT"
        self.sock.sendto(bytes(str(len(text)), encoding="utf8"), self.server)
        sequence_number = 0
        pozastavene = 0
        while True:
            # Čítanie fragmentu
            fragment_data = text[pozastavene:max_fragment_size-51 + pozastavene]
            pozastavene = max_fragment_size-51 + pozastavene
            if fragment_data == "":
                break  # Koniec súboru
            else:
                crc = binascii.crc_hqx(bytes(fragment_data, encoding="utf8"), 0)
                # Poslanie fragmentu s hlavičkou
                print(sequence_number + 1, "fragment bol odoslany s velkosotu", len(fragment_data) + 51)
                self.sock.sendto(struct.pack('!BII', 4, crc, sequence_number) + bytes(fragment_data, encoding="utf8"), self.server)
                # Očakávanie potvrdenia
                data, addr = self.sock.recvfrom(128)
                ack_sequence_number = struct.unpack('!I', data)[0]
                if ack_sequence_number == sequence_number:
                    sequence_number += 1
                else:
                    sequence_number = ack_sequence_number
                    pozastavene = pozastavene - max_fragment_size

            print("TEXT úspešne odoslaný")
        data, self.server = self.sock.recvfrom(128)
        if data == b"1":
            self.sock.sendto(b"7", (self.server_ip, self.server_port))
            data, self.server = self.sock.recvfrom(128)
            if data == b"10":
                port = self.sock.getsockname()[1]
                self.sock.close()
                # s = Server(socket.gethostbyname(socket.gethostname()), port)
                s = Server(socket.gethostbyname(socket.gethostname()), self.server_port)
                s.switcher()
        else:
            self.switcher()


class Server:
    def __init__(self, ip, port) -> None:
        self.client = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = ip
        self.port = port
        self.sock.bind((ip, port))

    def switcher(self):
        vstup, self.client = self.sock.recvfrom(128)
        if vstup == b"1":
            self.nadviazanie_spojenia(vstup, self.client)
        elif vstup == b"2":
            self.ukoncenie_spojenia(vstup, self.client)
        elif vstup == b"3":
            self.send_file()
        elif vstup == b"24":
            self.receive_text()
        elif vstup == b"34":
            self.send_text()
        elif vstup == b"7":
            self.sock.sendto(b"10", self.client)
            port = self.sock.getsockname()[1]
            self.sock.close()
            # c = Client(self.client[0], self.client[1])
            c = Client(self.client[0], port)
            time.sleep(1)
            c.nadviazanie_spojenia()
        elif int(str(vstup)[2]) == 0:
            global max_fragment_size
            max_fragment_size = int(str(vstup)[3:len(str(vstup)) - 1])
            self.switcher()
        elif vstup == b"6":  # KA
            self.sock.sendto(b"10", self.client)
            self.switcher()
        else:
            print(int(str(vstup)[2]))
            self.switcher()

    def nadviazanie_spojenia(self, data, client):
        if data == b"1":  # SYN
            self.sock.sendto(b"11", client)  # ACK,SYN
            data, self.client = self.sock.recvfrom(128)
            if data == b"10":
                print("Server: Spojenie nadviazane")
        else:
            print("Server: Spojenie nenadviazane")
        vymena = input("Server: Chces vymenit server/client? 1/0:")
        self.sock.sendto(bytes(vymena, encoding="utf8"), client)
        self.switcher()

    def ukoncenie_spojenia(self, data, client):
        if data == b"2":  # FIN
            self.sock.sendto(b"12", client)  # ACK,FIM
            data, self.client = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
            if data == b"10":  # ACK
                self.sock.close()
                print("Server: Spojenie ukoncene")
                return 1
            else:
                print("Server: Spojenie neukoncene")
        return 0

    def send_file(self):
        print("\n################Posielanie suboru################")
        self.sock.sendto(b"13", self.client)
        data, self.client = self.sock.recvfrom(128)
        if data == b"10":
            file_path, self.client = self.sock.recvfrom(128)
            self.sock.sendto(b"10", self.client)  # ACK
            # Otvorenie súboru na čítanie
            with open(file_path, 'rb') as file:
                print("Otvorenie suboru na citanie s nazvom: ",
                      str(os.path.basename(file_path))[2:len(str(os.path.basename(file_path))) - 1], "a cestou: ",
                      str(file_path)[2:len(str(file_path)) - 1], "a velkostou: ", os.path.getsize(file_path), "\n")
                sequence_number = 0
                test = True
                while True:
                    # Čítanie fragmentu zo súboru
                    fragment_data = file.read(max_fragment_size-51)
                    if not fragment_data:
                        break  # Koniec súboru
                    else:
                        # crc = self.crc_vypocet(fragment_data)
                        crc = binascii.crc_hqx(fragment_data, 0)
                        # Poslanie fragmentu s hlavičkou + chyba
                        if sequence_number == 2 and test:
                            test = False
                            print(4, "fragment bol odoslany s velkosotu", len(fragment_data) + 51)
                            # self.sock.sendto(struct.pack('!BII', 5, 50, 3) + fragment_data, self.client)#chybne crc
                            self.sock.sendto(struct.pack('!BII', 5, crc, 4) + fragment_data,
                                             self.client)  # chybne poradie
                        else:
                            print(sequence_number + 1, "fragment bol odoslany s velkosotu", len(fragment_data) + 51)
                            self.sock.sendto(struct.pack('!BII', 5, crc, sequence_number) + fragment_data, self.client)
                        # Očakávanie potvrdenia
                        data, self.client = self.sock.recvfrom(128)
                        if data == b"10":
                            sequence_number += 1
                        else:
                            sequence_number = int(str(data)[3:len(str(data)) - 1])
                            file.seek(sequence_number * len(fragment_data))

                print("\nSúbor úspešne odoslaný")
        vymena = input("Server: Chces vymenit server/client? 1/0:")
        self.sock.sendto(bytes(vymena, encoding="utf8"), self.client)
        self.switcher()

    def send_text(self):
        self.sock.sendto(b"14", self.client)
        text = "AHOJ JA SOM SERVER"
        self.sock.sendto(bytes(str(len(text)), encoding="utf8"), self.client)
        sequence_number = 0
        pozastavene = 0
        while True:
            # Čítanie fragmentu
            fragment_data = text[pozastavene:max_fragment_size-51 + pozastavene]
            pozastavene = max_fragment_size-51 + pozastavene
            if fragment_data == "":
                break  # Koniec súboru
            else:
                crc = binascii.crc_hqx(bytes(fragment_data, encoding="utf8"), 0)
                # Poslanie fragmentu s hlavičkou
                print(sequence_number + 1, "fragment bol odoslany s velkosotu", len(fragment_data) + 51)
                self.sock.sendto(struct.pack('!BII', 4, crc, sequence_number) + bytes(fragment_data, encoding="utf8"),
                                 self.client)
                # Očakávanie potvrdenia
                data, addr = self.sock.recvfrom(128)
                ack_sequence_number = struct.unpack('!I', data)[0]
                if ack_sequence_number == sequence_number:
                    sequence_number += 1
                else:
                    sequence_number = ack_sequence_number
                    pozastavene = pozastavene - max_fragment_size

            print("TEXT úspešne odoslaný")
        vymena = input("Server: Chces vymenit server/client? 1/0:")
        self.sock.sendto(bytes(vymena, encoding="utf8"), self.client)
        self.switcher()

    def receive_text(self):
        data, self.client = self.sock.recvfrom(128)
        if data == b"14":
            print("Server prijal poziadavku na prenos dat")
            velkost, self.client = self.sock.recvfrom(128)
            vel = int(str(velkost)[2:len(str(velkost)) - 1])
            expected_sequence_number = 0
            text = ""
            while True:
                # Prijatie fragmentu
                data, self.client = self.sock.recvfrom(max_fragment_size + HEADER_SIZE)
                # Overenie poradového čísla
                flag, crc, sequence_number = struct.unpack('!BII', data[:HEADER_SIZE])
                if len(text) < vel:
                    if sequence_number == expected_sequence_number and flag == 4 and crc == binascii.crc_hqx(
                            data[HEADER_SIZE:], 0):
                        # Zapísanie dát do súboru
                        text += str(data[HEADER_SIZE:])[2:len(str(data[HEADER_SIZE:])) - 1]
                        expected_sequence_number += 1
                        print(expected_sequence_number, "fragment bol prijaty s velkostou", len(data)+42)
                        # Poslanie potvrdenia o prijatí fragmentu
                        self.sock.sendto(struct.pack('!I', sequence_number), self.client)
                    else:
                        # Odozva na chybný fragment
                        self.sock.sendto(struct.pack('!I', expected_sequence_number), self.client)

                # Koniec prenosu
                if len(data) - 9 < max_fragment_size - 51:
                    break

            print("Sprava zo serveru: ", text)
        vymena = input("Server: Chces vymenit server/client? 1/0:")
        self.sock.sendto(bytes(vymena, encoding="utf8"), self.client)
        self.switcher()


if __name__ == "__main__":
    print("#################Inicializacia##################")
    #server = Server(socket.gethostbyname(socket.gethostname()), 10000)
    #server = Server(socket.gethostbyname(socket.gethostname()), int(input("Zadajte cielovy port: ")))
    client = Client(input("Zadajte cielovu ip adresu: "), int(input("Zadajte cielovy port: ")))
    print("################Zaciatok presonu################")
    #server.switcher()
    client.switcher()
