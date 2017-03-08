
import os
import sys
import time
import socket
import select
import argparse
import threading
import signal

from dschat.flask import app
from dschat.util.crypto import build_secret_key, encrypt


class ChatDaemon:
    def __init__(self):
        self.running = True
        self.broadcast_port = 5000
        self.broadcast_buffer = 1024
        
        self._parse_args()
        self.ip = self.args["ip"]
        self.secret = self.args["secret"]

        self._tlock = threading.Lock()

        self._t_comm = threading.Thread(target=self.broadcast)
        self._t_comm.daemon = True
        self._t_comm.start()

        while True:
            time.sleep(1)

    def _exit(self, exit_code):
        self.running = False
        if hasattr(self, "_t_comm"):
            self._t_comm.join()
        sys.exit(exit_code)

    def _parse_args(self):
        parser = argparse.ArgumentParser(prog="dschat", add_help=True)
        parser.add_argument("-d", "--debug", action="store_true", help="Enable debug")
        parser.add_argument("-i", "--ip", help="Bind to IP address")
        parser.add_argument("-s", "--secret", help="Shared secret")
        self.args = vars(parser.parse_args())

        if not self.args["ip"]:
            print("IP required")
            self._exit(1)

    def broadcast(self):
        bs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        bs.bind(("10.1.64.255", self.broadcast_port))
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bs.setblocking(0)

        ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ls.bind((self.ip, self.broadcast_port))
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.setblocking(0)

        magic = "DEADBEEF"
        discovery = "whoismaster|%s" % self.ip

        while self.running:
            try:
                bs.sendto(magic + "|" + discovery, ("10.1.64.255", self.broadcast_port))
            except socket.error as e:
                print(e)
                self._exit(1)

            time.sleep(1)

            try:
                data, addr = bs.recvfrom(self.broadcast_buffer)
            except socket.error as e:
                continue

            print(data)
            print(addr)

            if data:
                message = data.split("|")

                if message[0] == magic and message[1] == "whoismaster":
                    if message[2] != self.ip:
                        print("FOUND NEW NODE AT %s" % message[2])
                        ls.sendto("HELLO THERE", addr)

            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop

    def run(self):
        app.run(host="0.0.0.0", debug=True)
