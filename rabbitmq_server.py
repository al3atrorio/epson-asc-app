import pika
import json
from threading import Thread
from time import sleep
from collections import deque
from encryption import Encryption
from misc import Direction
#import messages_pb2

class RabbitMQ_Server():
	def __init__(self, dispatcher, config, mac, key):
		self.mac = mac
		self.config = config
		self.dispatcher = dispatcher

		self.credentials = pika.PlainCredentials(config["rabbitmq_login"], config["rabbitmq_password"])
		
		self.connected = False
		#self.message = messages_pb2.Code()

		self.encryption = Encryption(key)

		self._thread = Thread(target = self._receiver_thread)
		self._thread.start()


	def pooling_connect(self):
		self._thread_connection = Thread(target = self._connection_thread)
		self._thread_connection.start()

	def _connection_thread(self):
		while 1:
			print(" [*] RabbitMQ Server - Trying to Connect to RabbitMQ.")
			if self.connect():
				print(" [*] RabbitMQ Server - RabbitMQ unreachable.")
				sleep(1)
			else:
				break
		
		print(" [*] RabbitMQ Server - Connected to RabbitMQ.")

	def connect(self):
		try:
			self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.config["rabbitmq_server_ip"], credentials=self.credentials))
			self.channel = self.connection.channel()
			self.channel.exchange_declare(exchange='outbound.dojot.exchange', exchange_type='direct', durable=True)
			result = self.channel.queue_declare(exclusive=True)
			queue_name = result.method.queue
			self.channel.queue_bind(exchange='outbound.dojot.exchange', queue=queue_name, routing_key=self.mac)
			self.channel.basic_consume(self._receiver_callback, queue=queue_name, no_ack=True)
			self.connected = True
			
		except Exception as e:
			print(e)
			print(" [*] Could NOT connect to Rabbit Server. Network unreachable.")
			return 1

		return 0

	def _receiver_callback(self, ch, method, properties, body):
		#message.ParseFromString(body)
		try:
			print(" [*] RabbitMQ server received something.")
			json_message = self.encryption.decrypt(body)
			message = json.loads(json_message)
			self.dispatcher(message, Direction.InferDirection)
		except Exception as e:
			print(e)

	def _receiver_thread(self):
		print(' [*] RabbitMQ server created.')
		while 1:

			self.connected = False
			self.pooling_connect()

			while self.connected == False:
				sleep(0.5)
				
			try:
				self.channel.start_consuming()
			except:
				print(" [x] Rabbit server disconnected. Trying to reconnect...")

			



	def deinit(self):
		self.connection.close()
