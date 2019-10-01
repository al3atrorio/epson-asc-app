import pika
from encryption import Encryption
from time import sleep
from threading import Thread
from collections import deque
#import messages_pb2

class RabbitMQ_Client():
	def __init__(self, config, mac, key):
		self.mac = mac
		self.config = config
		self.credentials = pika.PlainCredentials(config["rabbitmq_login"], config["rabbitmq_password"])
		self.buffer = deque(maxlen=128)
		self.connected = False
		self.send_thread = Thread(target = self.send_messages_thread)

		self.send_thread.start()		
		self.pooling_connect()
		self.encryption = Encryption(key)

		print(" [*] RabbitMQ client created.")

	def send_messages_thread(self):
		while 1:
			while self.connected and len(self.buffer) > 0:
				message = self.buffer.popleft()
				
				if self.publish_to_rabbit(message) > 0:
					self.buffer.appendleft(message)
			
			sleep(0.01)

	def publish(self, message):
		self.buffer.append(message)

	def publish_to_rabbit(self, message):

		try:
			self.channel.basic_publish(exchange='inbound.dojot.exchange', routing_key=self.mac, body=self.encryption.encrypt(message))
		except Exception as e:
			print(e)
			print(" [*] Connection Closed. Trying to reconnect.")
			self.connected = False
			if self.connect():
				self.channel.basic_publish(exchange='inbound.dojot.exchange', routing_key=self.mac, body=message)
			else:
				self.pooling_connect()
				return 2

		print(f" [x] Sent {message} to server")

		return 0
	
	def pooling_connect(self):
		self._thread = Thread(target = self._connection_thread)
		self._thread.start()
	
	def _connection_thread(self):
		while 1:
			print(" [*] RabbitMQ Client - Trying to Connect to RabbitMQ.")
			if self.connect():
				print(" [*] RabbitMQ Client - RabbitMQ unreachable.")
				sleep(1)
			else:
				break
		
		print(" [*] RabbitMQ Client - Connected to RabbitMQ.")

	def connect(self):
		try:
			self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.config["rabbitmq_server_ip"], credentials=self.credentials, heartbeat_interval=30))
			self.channel = self.connection.channel()
			self.channel.exchange_declare(exchange='inbound.dojot.exchange', exchange_type='topic', durable=True)
			self.connected = True
		except:
			print(" [*] Could NOT connect to RabbitMQ. Network unreachable.")
			return 1
		
		return 0

	def deinit(self):
		self.connection.close()
