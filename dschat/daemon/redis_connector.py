import redis
import logging

log = logging.getLogger("dschat")


class Redis:

	def __init__(self,ip,port):
		log.info("Initializing redis-pubsub")
		self.r = redis.StrictRedis({'host':ip,'port':port,'db':0})
		self.s = r.pubsub()

	def publish(self,room,msg):
		self.r.publish(room,msg)

	def subscribe(self,room):
		self.s.subscribe(room)