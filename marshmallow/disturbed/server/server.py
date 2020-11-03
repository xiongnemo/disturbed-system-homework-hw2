from socketserver import ThreadingTCPServer, StreamRequestHandler, TCPServer
import struct
import threading
import socket
import sys
from enum import Enum
from marshmallow.disturbed.variables.text_search import construct_text_search_command
from marshmallow.disturbed.variables.server_status_template import server_status_template
from marshmallow.common.utils.files import is_file
from server_port import server_port
import os
import time


class ServerMode(Enum):
    UNINITIALIZED = 0
    WRITE = 1
    WAITING_FOR_QUERY = 2
    QUERYING = 3
    RECVING_BINARY_FILE = 4
    INITIAL_FILE_RECEIVED = 5
    FILE_LOADED = 6


current_server_mode = ServerMode.UNINITIALIZED
current_loaded_file_name = "NULL"
base_file_name = "NULL"


def receive_file() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Listens on specific port
        s.bind(('0.0.0.0', server_port + 1))
        # setup how many connection count it can listen to most(?)
        s.listen(10)
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print('[*] Server: 220 Waiting file transfer connection...')

    # wait for client..
    conn, addr = s.accept()

    print('[+] Server: 225 Data connection open; no transfer in progress.')
    print('[+] Server: 200 Accept new connection from {0}'.format(addr))
    conn.send('[+] Server: 200 Server ready to receive.'.encode('utf-8'))
    filename_received = "NULL"
    while 1:
        fileinfo_size = struct.calcsize('128sl')
        buf = conn.recv(fileinfo_size)
        if buf:
            # unpack the struct and get the information
            filename, filesize = struct.unpack('128sl', buf)
            fn = filename.strip(b'\00')
            fn = fn.decode()
            filename_received = str(fn)
            same_file_exist = False
            print(
                '[+] Server: 200 filename is {0}, filesize is {1}'.format(filename_received, filesize))
            # compare with the file existed (if)
            if is_file(filename_received):
                if os.stat(filename_received).st_size == filesize:
                    same_file_exist = True
                    conn.send('[+] Server: file exists!'.encode('utf-8'))

            if not same_file_exist:
                # receive the file
                conn.send('[-] Server: file needed.'.encode('utf-8'))
                print('[+] Server: 200 Transfer type changed to BINARY')
                recvd_size = 0
                fp = open('./' + str(fn), 'wb')
                print('[+] Server: 200 Start receiving...')

                # write..
                count = 0
                while not recvd_size == filesize:
                    if (count % 1000) == 0:
                        print(
                            '[+] Server: Received {0}%'.format(str(recvd_size / filesize * 100)))
                    count += 1
                    if filesize - recvd_size > 1024:
                        data = conn.recv(1024)
                        recvd_size += len(data)
                    else:
                        data = conn.recv(filesize - recvd_size)
                        recvd_size = filesize
                    fp.write(data)
                fp.close()
                print(
                    '[+] Server: 226 Closing data connection. Requested file action successful.')
        conn.close()
        break
    return filename_received


class MarshmallowHandler(StreamRequestHandler):
    def handle(self):
        print('[+] Server: 230 Got connection from', self.client_address)
        # self.rfile is a file-like object for reading
        for line in self.rfile:
            # self.wfile is a file-like object for writing
            if line[-1] == ord('\n'):
                line = line[:-1]
            print(line)
            if len(line) == 0:
                continue
            if line[0] == 0x01:
                if len(line) != 2:
                    self.wfile.write(
                        b"[-] Server: 451 Parameter Not Understood\n")
                else:
                    temp = b"[+] Server: 101 Switching Protocols\n"
                    if line[1] == 0x10:
                        self.wfile.write(
                            temp + b"[+] Server: 200 Entering write mode\n")
                        current_server_mode = ServerMode.WRITE
                    elif line[1] == 0x11:
                        self.wfile.write(
                            temp + b"[+] Server: 200 Entering query mode\n")
                        current_server_mode = ServerMode.WAITING_FOR_QUERY
                    elif line[1] == 0x12:
                        self.wfile.write(
                            temp + b"[+] Server: 200 Entering file transfer mode. Will listen on " + (str(server_port + 1)).encode('utf-8') + b".\n")
                        current_server_mode = ServerMode.RECVING_BINARY_FILE
                        current_loaded_file_name = receive_file()
                        print(
                            "[+] Server: 250 Requested file action okay, completed.")
                        current_server_mode = ServerMode.FILE_LOADED
                    else:
                        self.wfile.write(
                            temp + b"[-] Server: 202 Command not implemented, superfluous here.\n")
            elif line[0] == 0x02:
                print("[*] Server: generating status..")
                try:
                    str(current_server_mode)
                except UnboundLocalError:
                    current_server_mode = ServerMode.UNINITIALIZED
                    current_loaded_file_name = 'NULL'
                    base_file_name = "NULL"
                status = server_status_template.format(
                    str(current_server_mode), current_loaded_file_name, base_file_name)
                print(status)
                self.wfile.write(status.encode())
            elif line[0] == 0x03:
                if current_server_mode == ServerMode.WAITING_FOR_QUERY or current_server_mode == ServerMode.QUERYING:
                    current_server_mode = ServerMode.QUERYING
                    # can't use .decode() on single byte
                    data_id = chr(line[1])
                    author_name = line[2:].decode('utf-8')
                    print(
                        "[+] Server: 200 Author Name = {0}".format(author_name))
                    command_text = construct_text_search_command(
                        author_name, base_file_name + data_id)
                    query_start_time = time.time()
                    output = os.popen(command_text)
                    query_end_time = time.time()
                    answer = output.readlines()[0]
                    print("[+] Server: 200 Answer = {0}".format(answer))
                    print("cost {0} seconds".format(
                        query_end_time - query_start_time))
                    self.wfile.write(answer.encode())
                    current_server_mode = ServerMode.WAITING_FOR_QUERY
                else:
                    self.wfile.write(b"[-] Server: 451 Not in query mode.")
            elif line[0] == 0x04:
                print("[+] Server: 200 Preparing to switch file base name")
                base_file_name = line[1:].decode('utf-8')
                response = "[+] Server: 200 Base file name switched to " + \
                    base_file_name
                self.wfile.write(response.encode())
            elif line[0] == 0xff:
                self.wfile.write(b"[+] Server: 200 Bye.")
            else:
                self.wfile.write(line)


def run_server():
    serv = ThreadingTCPServer(('', server_port), MarshmallowHandler)
    print("[+] Server: listening on {0}".format(server_port))
    serv.serve_forever()


if __name__ == '__main__':
    run_server()
