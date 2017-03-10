
import os
import sys
import time
import socket
import select
import argparse
import threading
import signal

from dschat.flask.app.new_main import app, socketio
#from dschat.util.crypto import build_secret_key, encrypt


class ChatDaemon:
    def __init__(self):
        self.publishers=[]
        self.starttime=time.time()
        self.running = True
        self.broadcast_port = 5000
        self.zmq_pub_port=5001
        
        self.broadcast_buffer = 1024
        self.master=None
        
        self._parse_args()
        self.ip = self.args["ip"]
        self.secret = self.args["secret"]

        #self._tlock = threading.Lock()

        #self._t_comm = threading.Thread(target=self.broadcast)
        #self._t_comm.daemon = True
        #self._t_comm.start()

        #while True:
        #    time.sleep(1)
        self.run()
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
                bs.sendto(magic + "|" + discovery+"|"+"%d" %self.uptime(), ("10.1.64.255", self.zmq_pub_port))
            except socket.error as e:
                print(e)
                self._exit(1)

            time.sleep(1)

            try:
                data, addr = bs.recvfrom(self.broadcast_buffer)
            except socket.error as e:
                continue
            if (data, addr):
                self.communication(data,addr,s)    
            print(data)
            print(addr)

            if data:
                message = data.split("|")

                if message[0] == magic and message[1] == "whoismaster":
                    if message[2] != self.ip:
                        if self.uptime()<message[3]:
                            self.connectzmq(addr)

                        print("FOUND NEW NODE AT %s" % message[2])
                        ls.sendto("HELLO THERE", addr)

            #result = select.select([s], [], [])
            #print(result)
            # If response
            # Set up ZMQ
            # Fall back here means that if ZMQ disconnects, it will loop


    def uptime(self):
        return time.time()-self.starttime

        #every node is a publisher, and every node subscribes to every node.
    def pubzmq(self):
        c=zmq.Context()
        s=c.socket(zmq.PUB)
        s.bind("tcp://*:%s" %(self.zmq_pub_port))
        #while self.running:
            #check your local database, incase you receive a new input, send it to all subscribers
            #newmsg=database.checkforUpdates()
            #chatroom,message=newmsg.split("|")
            #s.send("%s|%s" %(chatroom,message))
            #print "published: %s|%s" %(chatroom,message)

    def subzmq(self,addr):
        context = zmq.Context()
        s = context.socket(zmq.SUB)
        for addr in self.publishers:
            s.connect("tcp://%s:%s",addr[0],addr[1])
        while self.running:
            msg=s.recv()
            chatroom,message=msg.split("|")
            
            #TODO: joku tän tyyppinen metodi tarvitaan tähän loppuun.
            #database.write(chatroom,message)



    def run(self):
        #app.run(host="0.0.0.0", debug=True)
        socketio.run(app, host="0.0.0.0", debug=True)
