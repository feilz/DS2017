
import sys
import time
import socket
import threading

from dschat.flask import app


class ChatDaemon:
    def __init__(self):
        self.running = True
        self.broadcast_port = 5000
        self._tlock = threading.Lock()

        self._t_comm = threading.Thread(target=self.broadcast)
        self._t_comm.start()

    def _exit(self, exit_code):
        self.running = False
        self._t_comm.join()

    def broadcast(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("10.1.64.51", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        magic = "DEADBEEF"

        while self.running:
            s.sendto(magic, ('<broadcast>', self.broadcast_port))
            time.sleep(2)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop

    def run(self):
        app.run(host="0.0.0.0", debug=True)
