import struct
import time
import sys
from threading import Thread
from collections import deque
from time import sleep
import keymap


class keyboardDevice:
	def __init__(self, device):
		self._codes = deque(maxlen=128)
		self._device = device
		self._format = 'llHHI'
		self._eventSize = struct.calcsize(self._format)		
		self._codestring = ""
		self._shift = False
		self.active = False
		self.disabled = False

		self._thread = Thread(target = self.readcodeloop)
		self._thread.start()
	
	def close(self):
		if self._in_file != None:
			self._in_file.close()

	def hasCodeToRead(self):
		return len(self._codes) > 0

	def getcode(self):
		return self._codes.pop()

	def getdevice(self):
		return self._device

	def readcodeloop(self):
		counter = 0

		try:
			self._in_file = open(self._device, "rb")
			self.active = True
		except Exception as e:
			print( " [x] Could not open Usb device.")
			return

		while 1:

			try:
				event = self._in_file.read(self._eventSize)
			except Exception as e:
				print(" [x] Fail to read Usb device")
				print(e)
				self.active = False
			
			if self.active == False:
				print(" [x] Trying to reconnect.")
				for i in range(3):
					try:
						self._in_file = open(self._device, "rb")
						self.active = True
						counter = 0
						print(" [*] Usb device Reconnected.")
						break
					except Exception as e:
						counter += 1
						if counter > 3:
							print(" [x] Could not reconnect to device. Removing")
							self.disabled = True
							return
						else:
							time.sleep(0.5)
						
				continue

			(tv_sec, tv_usec, type, code, value) = struct.unpack(self._format, event)

			if type == 1 and value == 1:
				if code == keymap.KEY_ENTER:
					self._codes.append(self._codestring)
					self._codestring = ""
				elif code == keymap.KEY_LEFTSHIFT:
					self._shift = True
				else:
					self._codestring += keymap.keymap[code].upper() if self._shift else keymap.keymap[code]

			if type == 1 and value == 0:
				if code == keymap.KEY_LEFTSHIFT:
					self._shift = False

			


