#!coding=utf-8

import sys
import socket
import time
import math
from typing import List
import concurrent.futures
import socket
import os
import sys
import struct
from marshmallow.disturbed.variables.split_file import construct_split_file_command
from marshmallow.common.utils.files import is_file
from marshmallow.disturbed.variables.header import print_header
from marshmallow.common.variables.terminal_colors import bcolors
from course_logging import echo_to_log
from server_config import server_address_list

class ServerReturnNullError(Exception):
    pass

def socket_send_and_get_result(s: socket, data: str) -> str:
    s.send(data.encode())
    recvd_data = s.recv(1024)
    res = recvd_data.decode()
    print(res)


def socket_get_result(s: socket) -> str:
    recvd_data = s.recv(1024)
    res = recvd_data.decode()
    print(res)
    return res


def socket_get_result_sliently(s: socket) -> str:
    recvd_data = s.recv(1024)
    res = recvd_data.decode()
    return res


class DisturbedServer:
    def __init__(self, ip: str, main_port_num: int, server_data_id: str):
        self.ip = ip
        self.main_port_num = main_port_num
        self.server_data_id = server_data_id
        self.server_id = server_data_id
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_socket.connect((ip, main_port_num))
        self.socket = temp_socket

    def bye(self):
        a = b'\xff\n'
        self.socket.send(a)
        recvd_data = self.socket.recv(1024)
        res = recvd_data.decode()
        print(res)
        self.socket.close()


def send_file(filepath: str, server: DisturbedServer):
    ip = server.ip
    file_transfer_port = server.main_port_num + 1
    try:
        print("[*] Client: trying to establish file socket connection..")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, file_transfer_port))
    except socket.error as msg:
        print(msg)
        sys.exit(1)
    print(s.recv(1024).decode('utf-8'))

    if os.path.isfile(filepath):
        # use struct to define a struct that contains file_name and file_size
        fhead = struct.pack('128sl', os.path.basename(
            filepath).encode('utf-8'), os.stat(filepath).st_size)
        s.send(fhead)
        # now the server scans for the exact file. if file with exact name and size exists then..
        if socket_get_result(s) == "[+] Server: file exists!":
            print(bcolors.OKCYAN + "[+] Client: remote file exists!" + bcolors.ENDC)
        else:
            # send file through socket
            fp = open(filepath, 'rb')
            while 1:
                data = fp.read(1024)
                if not data:
                    print('[+] {0}: file send over...'.format(
                        os.path.basename(filepath)))
                    break
                s.send(data)
        s.close()


def send_file_through_socket(filepath: str, server: DisturbedServer):
    print(
        "[*] Client: will send {0} to Server #{1}".format(filepath, server.server_id))
    sock = server.socket
    a = '\x01\x12\n'
    sock.send(a.encode())
    socket_get_result(sock)
    send_file(filepath, server)
    return True


def check_status(server: DisturbedServer) -> bool:
    print(
        "[*] Client: will check status for Server #{0}".format(server.server_id))
    sock = server.socket
    a = '\x02\n'
    sock.send(a.encode())
    print(
        "[*] Client: waiting to get result from #{0}".format(server.server_id))
    try:
        response = socket_get_result(sock)
        if response == "":
            print()
            raise ServerReturnNullError()
        return True
    except:
        return False


def switch_to_query(server: DisturbedServer):
    sock = server.socket
    a = '\x01\x11\n'
    sock.send(a.encode())
    socket_get_result(sock)


def switch_base_file_name(base_file_name: str, server: DisturbedServer):
    sock = server.socket
    a = '\x04' + base_file_name + '\n'
    sock.send(a.encode())
    socket_get_result(sock)


def query(author_name: str, server: DisturbedServer, data_id: str) -> int:
    sock = server.socket
    a = '\x03' + data_id + author_name + '\n'
    sock.send(a.encode())
    answer = socket_get_result_sliently(sock)
    return int(answer)


def query_through_server_list(author_name: str, server_list: List[DisturbedServer]) -> int:
    result = 0
    for server in server_list:
        result += query(author_name, server)
    print(
        "[+] Client: {0}'s overall result = {1}".format(author_name, str(result)))
    return result


def run_client():
    print("[*] Client: initializing")
    echo_to_log("client startup.")
    server_a = DisturbedServer(server_address_list[0][0], server_address_list[0][1], "a")
    server_b = DisturbedServer(server_address_list[1][0], server_address_list[1][1], "b")
    # server_c = DisturbedServer("127.0.0.1", 21360, "c")
    server_c = DisturbedServer(server_address_list[2][0], server_address_list[2][1], "c")
    server_list = [server_a, server_b, server_c]
    all_server_list = [server_a, server_b, server_c]
    file_name = input(
        "[*] Client: initial filename needed.\n(dblp_orig.xml)>? ")
    if not is_file(file_name):
        file_name = "dblp_orig.xml"
        # file_name = input("[*] Client: Provide a legal filename.\n>? ")
    if not (is_file(file_name + "aa") and is_file(file_name + "ab") and is_file(file_name + "ac")):
        print("[*] Client: spliting file")
        command_text = construct_split_file_command(3, file_name)
        os.popen(command_text)
    print(bcolors.OKGREEN + "[+] Client: file splitted" + bcolors.ENDC)
    for server in server_list:
        check_status(server)

    print("[*] Client: sending replicas")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        t_1 = executor.submit(send_file_through_socket,
                              file_name + "ab", server_a)
        t_2 = executor.submit(send_file_through_socket,
                              file_name + "ac", server_b)
        t_3 = executor.submit(send_file_through_socket,
                              file_name + "aa", server_c)
        return_value_1 = t_1.result()
        return_value_2 = t_2.result()
        return_value_3 = t_3.result()
        print(return_value_1)
        print(return_value_2)
        print(return_value_3)

    print("[*] Client: sending files")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        t_1 = executor.submit(send_file_through_socket,
                              file_name + "aa", server_a)
        t_2 = executor.submit(send_file_through_socket,
                              file_name + "ab", server_b)
        t_3 = executor.submit(send_file_through_socket,
                              file_name + "ac", server_c)
        return_value_1 = t_1.result()
        return_value_2 = t_2.result()
        return_value_3 = t_3.result()
        print(return_value_1)
        print(return_value_2)
        print(return_value_3)

    data_map = {
        "a": [server_a, server_c],
        "b": [server_b, server_a],
        "c": [server_c, server_b],
    }

    # send_file_through_socket(file_name + "aa", server_a)
    # send_file_through_socket(file_name + "ab", server_b)
    # send_file_through_socket(file_name + "ac", server_c)
    print(bcolors.OKGREEN + "[+] Client: file sent successfully" + bcolors.ENDC)
    splited_file_name_base = file_name + "a"
    for server in server_list:
        splited_file_name_base = file_name + "a"
        switch_base_file_name(splited_file_name_base, server)
        check_status(server)

    switch_to_query(server_a)
    switch_to_query(server_b)
    switch_to_query(server_c)
    for server in server_list:
        check_status(server)

    def check_server_status() -> bool:
        print("[*] Client: Checking all server's status..")
        for server in all_server_list:
            up_status = check_status(server)
            if not up_status and (server in server_list):
                print(bcolors.FAIL + "[-] Client: Server #{0} seems to be offline!".format(server.server_id) + bcolors.ENDC)
                server_list.remove(server)
                for data_id in data_map:
                    try:
                        data_map[data_id].remove(server)
                    except ValueError:
                        pass
        if len(server_list) < 2:
            print(bcolors.FAIL + "[-] Client: Can't fulfill the need." + bcolors.ENDC)
            return False
        print("[*] Client: Checking alive server's files..")
        for data_id in data_map:
            for server in data_map[data_id]:
                send_file_through_socket(splited_file_name_base + data_id, server)
                switch_to_query(server)
        return True
    
    # query_through_server_list("Hans Uszkoreit", server_list)
    while True:
        print_header()
        op = input("operation?\n> ")
        if op == '1':
            if not check_server_status():
                break
            # Hans Uszkoreit
            author_name = input("author name?\n> ")
            query_start_time = time.time()
            echo_to_log("query started.")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                t_1 = executor.submit(query, author_name,
                                      data_map["a"][0], "a")
                t_2 = executor.submit(query, author_name,
                                      data_map["b"][0], "b")
                t_3 = executor.submit(query, author_name,
                                      data_map["c"][0], "c")
                return_value_1 = t_1.result()
                return_value_2 = t_2.result()
                return_value_3 = t_3.result()
                print("{0}: answer is {1}".format(
                    server_a.server_data_id, return_value_1))
                print("{0}: answer is {1}".format(
                    server_b.server_data_id, return_value_2))
                print("{0}: answer is {1}".format(
                    server_c.server_data_id, return_value_3))
                query_end_time = time.time()
                answer = return_value_1 + return_value_2 + return_value_3
                print(bcolors.BOLD + bcolors.OKGREEN + "{0}: answer is {1}".format(author_name, answer) + bcolors.ENDC)
                print("cost {0} seconds".format(
                    query_end_time - query_start_time))
                echo_to_log("query for {0}: answer is {1}, get in {2} seconds of time".format(author_name, answer, query_end_time - query_start_time))
                
        elif op == '2':
            if not check_server_status():
                break
        elif op == '3':
            break
        else:
            print(bcolors.FAIL + "[-] Client: Please, at least choose an option." + bcolors.ENDC)
    for server in server_list:
        server.bye()
    echo_to_log("client shutdown complete.")
    print(bcolors.OKCYAN + "[+] Client: Bye." + bcolors.ENDC)


if __name__ == '__main__':
    run_client()
