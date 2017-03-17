
import os
import sys
import time
import socket
import select
import argparse
import threading
import zmq
import multiprocessing

from dschat.util.timeutils import *
#from dschat.util.crypto import build_secret_key, encrypt


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
            tstamp = create_timestamp()
            datetime = ts_to_datetime(tstamp)
            unix_time = ts_to_unix(tstamp)

            message = {}
            message["content"] = {"msg": "This is a test message"}
            message["room"] = "asd"

            yield message

    def run(self):
        print("hello")
        #zmqhandlers(self.ip,self.zmq_pub_port)
        self._tlock = threading.Lock()

        self.broadcast()

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
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bs.setblocking(0)
        bs.bind(("10.1.64.255", self.broadcast_port))

        ls = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        ls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ls.setblocking(0)
        ls.bind((self.ip, self.broadcast_port))

        magic = "DEADBEEF"
        discovery = "whoismaster|%s" % self.ip

        counter = 0
        max_tries = 5

        while self.running:
            while counter < max_tries:
                try:
                    bs.sendto(magic + "|" + discovery+"|"+"%d" %self.uptime(), ("10.1.64.255", self.zmq_pub_port))
                except socket.error as e:
                    print(e)
                    self._exit(1)

                time.sleep(1)

                while True:
                    try:
                        data, addr = bs.recvfrom(self.broadcast_buffer)
                    except socket.error as e:
                        break

                    if (data, addr):
                        print(data)
                        print(addr)

                    if data:
                        message = data.split("|")

                        if message[0] == magic and message[1] == "whoismaster":
                            if message[2] != self.ip:
                                self.nodes.append((addr, message[2]))
                                print(self.nodes)
                                #zmqhandlers.connectsub(addr)
                                #print("FOUND NEW NODE AT %s" % message[2])
                                #ls.sendto("HELLO THERE", addr)

            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop


    def uptime(self):
        return time.time()-self.starttime

    def run(self):
        self.broadcast()
        #app.run(host="0.0.0.0", debug=True)
        #socketio.run(app, host="0.0.0.0", debug=True)

class zmqhandlers:

    def __init__(self,ip,port):
        self.context=zmq.Context()
        self.pub=self.context.socket(zmq.PUB)
        self.pub.bind("tcp://%s:%s" %(ip,port))
        self.sub=self.context.socket(zmq.SUB)
        j = multiprocessing.Process(target=self.receive)
        j.start()

    def publish(self,msg):
        self.pub.send(msg)

    def connectsub(self,addr):
        self.sub.connect("tcp://%s:%s" %(addr[0],addr[1]))

    def receive(self):
        while ChatDaemon.running:
            msg = self.sub.recv()
            print msg
            #database.write(msg)
    #def __exit___(self):
    #	self.context.term()

    #def __enter___(self):
