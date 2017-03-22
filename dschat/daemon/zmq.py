import zmq


class ZMQ:
    def __init__(self,ip,port):
        self.context=zmq.Context()
        self.pub=self.context.socket(zmq.PUB)
        self.pub.bind("tcp://%s:%s" %(ip,port))
        self.sub=self.context.socket(zmq.SUB)
        
    def publish(self,msg):
        self.pub.send(msg)

    def connectsub(self,addr):
        self.sub.connect("tcp://%s:%s" %(addr[0],addr[1]))

    #def __exit___(self):
    #	self.context.term()

    #def __enter___(self):
