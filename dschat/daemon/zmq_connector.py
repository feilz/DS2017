import zmq
import logging
#from gevent_zeromq import zmq

log = logging.getLogger("dschat")

class ZMQ:
    def __init__(self,ip,port):
        log.info("Initializing ZMQ-connector")
        self.context = zmq.Context()
        self.pub = self.context.socket(zmq.PUB)
        self.pub.bind("tcp://%s:%s" % (ip, port))
        self.sub = self.context.socket(zmq.SUB)
        self.sub.setsockopt(zmq.SUBSCRIBE, "")

    def publish(self, msg):
        log.info("Publishing to all nodes")
        self.pub.send(msg)

    def connectsub(self, addr):
        log.info("Trying to connect to %s" %(addr[0]))
        try:
            self.sub.connect("tcp://%s:%s" %(addr[0], addr[1]))
            log.info("Success")
            return True
        except zmq.socket.error:
            log.error("Fail") 
            return False

    #def __exit___(self):
    #	self.context.term()

    #def __enter___(self):
