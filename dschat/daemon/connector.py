
import sys
import time
import socket
import argparse

from dschat.util.timeutils import *
from dschat.daemon.zmq_connector import ZMQ


class Connector():
    def __init__(self):
        self.starttime=time.time()
        self.running = True
        
        self.broadcast_buffer = 1024
        self.broadcast_port = 4000
        self.master=None
        self.zmq_pub_port=5001

        self.nodes = []
        
        self._parse_args()
        self.ip = self.args["ip"]
        self.secret = self.args["secret"]

    def __enter__(self):
        #self.broadcast()
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def next_message(self):
        while True:
            #zmqmsg=None
            tstamp = create_timestamp()
            datetime = ts_to_datetime(tstamp)
            unix_time = ts_to_unix(tstamp)
            message = {}
            print("BBBBB")
            try:
                #zmqmsg=self.zmq.sub.recv(flags=zmq.NOBLOCK)
                #message['datetime']=zmqmsg['datetime']

                message["content"] = {"msg": "This is a test message"}
                print("AAAAA")
                message["room"] = "asd"
            except zmq.Again as e:
                pass
           
            yield message

    def connect(self, master=None):
        if not master:
            master = self.broadcast()

        self.zmq = ZMQ(self.ip, self.zmq_pub_port)

        if master != self.ip:
            self.zmq.connectsub(master)

    def _exit(self, exit_code):
        self.running = False
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
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bs.settimeout(1)
        bs.bind(("10.1.64.255", self.broadcast_port))

        ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.bind((self.ip, self.broadcast_port))

        magic = "DEADBEEF"
        discovery = "whoismaster|%s" % self.ip

        counter = 0
        max_tries = 3

        master = None
        nodes = []

        while self.running:
            while counter < max_tries:
                try:
                    ls.sendto(magic + "|" + discovery+"|"+"%d" %self.uptime(), ("10.1.64.255", self.broadcast_port))
                except socket.error as e:
                    print(e)
                    self._exit(1)

                time.sleep(1)

                try:
                    data, addr = bs.recvfrom(self.broadcast_buffer)

                    if (data, addr):
                        print(data)
                        print(addr)

                    if data:
                        message = data.split("|")

                        if message[0] == magic and message[1] == "whoismaster":
                            print(message)
                            if addr[0] != self.ip:
                                if (addr, message[3]) not in nodes:
                                    nodes.append((addr, message[3]))
                                #zmqhandlers.connectsub(addr)
                                #print("FOUND NEW NODE AT %s" % message[2])
                                #ls.sendto("HELLO THERE", addr)

                except socket.error as e:
                    pass

                counter += 1
                
            print(nodes)
            counter = 0

            if nodes:
                return nodes[0][0]

            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop


    def uptime(self):
        if not hasattr(self, "time_now"):
            self.time_now = time.time()

        return self.time_now - self.starttime
