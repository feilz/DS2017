
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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((self.ip, self.broadcast_port))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setblocking(0)

        magic = "DEADBEEF"
        discovery = "new|%s" % self.ip

        while self.running:
            try:
                s.sendto(magic + discovery, ('<broadcast>', self.broadcast_port))
            except socket.error as e:
                print("AAA")
                print(e)
                self._exit(1)

            time.sleep(1)

            try:
                data, addr = s.recvfrom(self.broadcast_buffer)
            except socket.error as e:
                continue

            print(data)
            print(addr)
            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop

    def run(self):
        app.run(host="0.0.0.0", debug=True)
