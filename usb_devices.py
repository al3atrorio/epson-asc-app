import json
from threading import Thread
from time import sleep
from keyboard_device import keyboardDevice
from misc import Direction

class UsbDevices:
	def __init__(self, dispatcher):
		self.usb_readers = {}
		self.dispatcher = dispatcher

		self._read_thread = Thread(target = self._deviceThread)
		self._read_thread.start()

		self._monitor_thread = Thread(target = self.usb_monitor)
		self._monitor_thread.start()

	def usb_monitor(self):
		while 1:
			try:
				current_readers = self.parseReadersData()
				self.updateReadersIfNeeded(current_readers)
			except Exception as e:
				print(e)
				
			sleep(3)
	
	def parseReadersData(self):
		current_readers = {}

		with open ("/proc/bus/input/devices", "r") as myfile:
			data = myfile.read().split("\n\n") #split by empty line

		for line in data:
			pos = line.find('usb2/2-')
			if pos != -1:
				pos_event = line.find('event')
				event = line[pos_event:pos_event+9].split()[0]
				port = f"usb{line[pos+7]}"
				
				current_readers[port] = event
		
		return current_readers
	
	def updateReadersIfNeeded(self, current_readers):
		device_to_remove = []
		for port, event in self.usb_readers.items():
			if port not in current_readers or event.disabled == True:
				event.close()
				print(f"Removing device on port {port}")
				device_to_remove.append(port)

		for i in device_to_remove:
			del self.usb_readers[i]
		
		for port, event in current_readers.items():
			if port not in self.usb_readers:
				print(f"Adding device on port {port}")				
				self.usb_readers[port] = keyboardDevice("/dev/input/" + event)


	def _deviceThread(self):
		print(" [*] Usb Device Thread Created.")
		while 1:
			for port, device in self.usb_readers.items():
				if device.hasCodeToRead():
					message = {
						"type": "usb_device",
						"connection": port,
						"payload": {
							"value": device.getcode()
						}
					}

					self.dispatcher(message, Direction.ToDojot)
			
			sleep(0.02)

