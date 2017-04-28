from gevent import monkey
monkey.patch_all()

import gevent
from gevent.pool import Pool

import sys
import zmq
import time
import socket
import argparse
import multiprocessing
import logging

from dschat.util.crypto import *
from dschat.util.timeutils import *
from dschat.daemon.redis_connector import Redis 

log = logging.getLogger("dschat")


class Connector():
    def __init__(self):
        log.info("Initializing Connector")
        self.starttime=create_timestamp()
        self.running = True
        
        self.broadcast_buffer = 1024
        self.broadcast_port = 4000
        self.master=None
        #self.zmq_pub_port=5001
        self.redis_port=6379
        self.nodes = {}
        self.lock = multiprocessing.Lock()
        self.connectedNodes=[]
        self._parse_args()
        self.ip = self.args["ip"]
        self.redis_ip = self.args["redis"]
        self.secret = self.args["secret"]
        if self.secret:
            log.info("Encryption mode enabled")
            self.secret = build_secret_key(self.secret)

        self.redis = Redis(self.redis_ip, self.redis_port)

    def __enter__(self):
        #self.broadcast()
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def next_message(self):
        while True:
            time.sleep(0.1)

            try:
                message = self.redis.s.get_message()
            except AttributeError:
                yield None

            if not message or message["data"] == 1L:
                yield None

            else:
                yield message["data"]


    def connect(self, nodes=None):
        _broadcast=multiprocessing.Process(target=self.broadcast)
        _broadcast.start()
        """if not nodes:
            ls, bs, self.nodes = self.broadcast()

        #nodeConnector=multiprocessing.Process(target=self.connectToNodes)
        #nodeConnector.start()
        #bgListener=multiprocessing.Process(target=self.backgroundListener,args=(bs,ls,))
        #bgListener.start()
        #_pool = Pool(10)
        #_pool.apply_async(func=self.connectToNodes)
        #_pool.apply_async(func=self.backgroundListener,args=(bs,ls))
        log.info("Connecting to discovered nodes")
        nodeConnector=gevent.spawn(self.connectToNodes)
        bgListener=gevent.spawn(self.backgroundListener,bs,ls)
        print("AAAAAAA")
        gevent.sleep(0)
        #_pool.join()
        #nodeConnector.join()
        #bgListener.join()"""   
        print("BBBBBBB")
        
    def connectToNodes(self):
        while self.running:
            with self.lock:
                for node in self.nodes:
                    print("ZMQ connecting to %s" % node[0])
                    log.info("Starting connecting to address %s" %(node[0]))
                    if self.zmq.connectsub((node[0], self.zmq_pub_port)):
                        self.nodes.remove(node)
            time.sleep(1)


    def _exit(self, exit_code):
        self.running = False
        sys.exit(exit_code)

    def _parse_args(self):
        parser = argparse.ArgumentParser(prog="dschat", add_help=True)
        parser.add_argument("-d", "--debug", action="store_true", help="Enable debug")
        parser.add_argument("-i", "--ip", help="Bind to IP address")
        parser.add_argument("-r", "--redis", help="Redis server IP address")
        parser.add_argument("-s", "--secret", help="Shared secret")
        self.args = vars(parser.parse_args())

        if not self.args["ip"]:
            print("IP required")
            self._exit(1)

    def broadcast(self):
        log.info("Starting initial broadcasting")
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
        discovery = "ONLINE|%s" % self.ip

        while self.running:
            try:
                ls.sendto(magic + "|" + discovery+"|"+"%d" % create_timestamp(), ("10.1.64.255", self.broadcast_port))
            except socket.error as e:
                print(e)
                self._exit(1)

            time.sleep(1)

            try:
                data, addr = bs.recvfrom(self.broadcast_buffer)

                if data:
                    message = data.split("|")

                    if message[0] == magic:
                        if message[1] == "ONLINE":
                            if addr[0] != self.ip:
                                if addr[0] not in self.nodes.keys():
                                    with self.lock:
                                        log.info("Ńode %s added to list" % addr[0])
                                        # Add timestamp to the node list
                                        self.nodes[addr[0]] = message[3]

            except socket.error as e:
                pass

            for i,j in self.nodes.items():
                print(j)
                print(create_timestamp())
                if int(j) <= int(create_timestamp()) - 15:
                    log.info("Node %s has not been seen for 15 seconds. Marking host as OFFLINE" % i)
                    del self.nodes[i]
                    

    def backgroundListener(self,bs,ls):
        magic="DEADBEEF"
        discovery="whoismaster|%s" %self.ip
        log.info("Initializing backgroundlistener for new nodes")
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
                                with self.lock:
                                    self.nodes.append(addr)
            except socket.error as e:
                time.sleep(1)
                pass
        log.info("BackgroundListener shutting down")
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
