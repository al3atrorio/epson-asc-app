import json
from time import sleep
from threading import Thread

from misc import Direction
from config import Config
from usb_devices import UsbDevices
from rabbitmq_client import RabbitMQ_Client
from rabbitmq_server import RabbitMQ_Server
from leds import Leds
from gpios import Gpios
from display import Displays
from rfid import Rfid
from lwm2m import Lwm2m
from state import State
from monitor import Monitor

class Application:

	def __init__(self):
		print(" [*] Application starting")

		self.status = 'valid'

		self.config = Config()
		self.status = self.config.status
		
		self.rabbit_client = RabbitMQ_Client(self.config.rabbitmq, self.config.mac, self.config.amqp_encryption_key)
		self.rabbit_server = RabbitMQ_Server(self.dispatch, self.config.rabbitmq, self.config.mac, self.config.amqp_encryption_key)
		self.usb_devices = UsbDevices(self.dispatch)
		self.leds = Leds()
		self.gpios = Gpios(self.dispatch)
		self.displays = Displays(self.dispatch)
		self.rfids = Rfid(self.dispatch)
		self.lwm2m = Lwm2m(self.config)
		self.state = State(self.dispatch)
		self.monitor = Monitor(self.dispatch, self.config)

	def run(self):
		print(" [*] Application running")

		#Application main loop
		while 1:
			sleep(0.1)

	def inferDirection(self, message):
		if message["type"] == "led":
			return Direction.ToLeds
		elif message["type"] == "gpio":
			return Direction.ToGpios
		elif message["type"] == "display":
			return Direction.ToDisplays
		else:
			print(" [x] Couln't infer direction!")
			return Direction.Unknown

	def validateMessage(self, message):
		if type(message) is not dict:
			print(" [x] Invalid message. Message is not a dict: " + str(message))
			return 1
		
		if "type" not in message:
			print(" [x] Invalid message. Message has no type: " + str(message))
			return 2

		return 0

	def dispatch(self, message, direction, save=True):

		if self.validateMessage(message) != 0:
			print(" [x] Dropping invalid message")
			return

		if direction == Direction.InferDirection:
			direction = self.inferDirection(message)

		if direction == Direction.ToDojot:
			self.rabbit_client.publish(json.dumps(message))
		elif direction == Direction.ToLeds:
			self.leds.process_message(message)
			if save: self.state.saveState(message)
		elif direction == Direction.ToGpios:
			self.gpios.process_message(message)
			if save: self.state.saveState(message)
		elif direction == Direction.ToDisplays:
			self.displays.process_message(message)
			if save: self.state.saveState(message)
		else:
			print(" [x] Invalid message or destination. No information to route it!")
