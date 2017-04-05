import sys
import zmq
import time
import socket
import argparse
import multiprocessing

from dschat.util.crypto import *
from dschat.util.timeutils import *
from dschat.daemon.zmq_connector import ZMQ


class Connector():
    def __init__(self):
        self.starttime=create_timestamp()
        self.running = True
        
        self.broadcast_buffer = 1024
        self.broadcast_port = 4000
        self.master=None
        self.zmq_pub_port=5001

        self.nodes = []
        
        self._parse_args()
        self.ip = self.args["ip"]
        self.secret = self.args["secret"]
        if self.secret:
            self.secret = build_secret_key(self.secret)

        self.zmq = ZMQ(self.ip, self.zmq_pub_port)

    def __enter__(self):
        #self.broadcast()
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def next_message(self):
        while True:
            message = None

            try:
                message = self.zmq.sub.recv(flags=zmq.NOBLOCK)
            except zmq.Again as e:
                pass
           
            yield message

    def connect(self, nodes=None):
        if not nodes:
            ls, bs, self.nodes = self.broadcast()

        for node in self.nodes:
            print("ZMQ connecting to %s" % node[0])
            self.zmq.connectsub((node[0], self.zmq_pub_port))

        bgListener=multiprocessing.Process(target=self.backgroundListener,args=(bs,ls,))
        bgListener.start()

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

        nodes = []

        while self.running:
            while counter < max_tries:
                try:
                    ls.sendto(magic + "|" + discovery+"|"+"%d" %self.starttime, ("10.1.64.255", self.broadcast_port))
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
                                if addr not in nodes:
                                    nodes.append(addr)
                                #zmqhandlers.connectsub(addr)
                                #print("FOUND NEW NODE AT %s" % message[2])
                                #ls.sendto("HELLO THERE", addr)

                except socket.error as e:
                    pass

                counter += 1
                
            print(nodes)
            counter = 0

            if nodes:
                return ls,bs,nodes

    def backgroundListener(self,bs,ls):
        magic="DEADBEEF"
        discovery="whoismaster|%s" %self.ip
        while self.running:
            print("HERE")
            try:
                data,addr=bs.recvfrom(self.broadcast_buffer)
                if (data,addr):
                    print(data)
                    print(addr)
                if data:
                    msg = data.split("|")
                    if msg[0]==magic and msg[1]=="whoismaster":
                        print(msg)
                        if addr[0]!=self.ip:
                            if addr not in self.nodes:
                                print("ZMQ connecting to %s" % addr[0])
                                print("AAAAAAA")
                                print(addr)
                                print(addr[0])
                                print(self.nodes)
                                print(msg)
                                print("AAAAAAA")
                                ls.sendto(magic + "|" + discovery+"|"+"%d" %self.starttime, ("10.1.64.255", self.broadcast_port))
                                self.zmq.connectsub((addr[0], self.zmq_pub_port))
                                self.nodes.append(addr)
            except socket.error as e:
                time.sleep(1)
                pass
        ls.shutdown()
        ls.close()
        bs.shutdown()
        bs.close()

#####
#            oldest_node = None

            #for node in nodes:
            #    if not oldest_node:
            #        oldest_node = node
            #        continue
#
#                if node[1] < oldest_node[1]:
#                    oldest_node = node
#
#            if oldest_node[1] < self.starttime:
#                # I am node
#                return oldest_node[0][0]
#
#            else:
#                # I am master
#                return self.ip
#####

            #if nodes:
            #    return nodes[0][0]

            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop
