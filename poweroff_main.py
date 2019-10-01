from time import sleep

from display import Displays
from misc import Direction

class PowerOffApp:
	'''
	Turn off the display (backlight, leds, sound and text)
	This code is based on application.py
	'''
	def __init__(self):
		print(" [*] Application starting")

		self.displays = Displays(self.dispatch)

	def run(self):
		print(" [*] Poweroff")

		# Wait until the displays are identified
		while len(self.displays.display_types) == 0:
			sleep(0.1)

		# Turn off the displays that are connected
		for i,disp_type in enumerate(self.displays.display_types, start=1):
			if disp_type != None:
				message = {
					"type": "display",
					"connection": f"display{i}",
					"payload": {
						"screen1": {
							"options": {
								"clear_screen": True
							}
						}, # screen1
						"screen2": {
							"options": {
								"clear_screen": True
							}
						}, # screen2
						"screen3": {
							"options": {
								"clear_screen": True
							}
						}, # screen3
						"screen4": {
							"options": {
								"clear_screen": True
							}
						}, # screen4
						"backlight": {
							"value": "off",
						}, # backlight
						"leds": {
							"led1": {
								"value": "off"
							},
							"led2": {
								"value": "off"
							},
							"led3": {
								"value": "off"
							},
							"led4": {
								"value": "off"
							},
							"led5": {
								"value": "off"
							},
							"led6": {
								"value": "off"
							},
						}, # leds
						"sound" : {
							"reps": 1,
							"active_time": 1,
							"inactive_time": 1,
						}, # sound
					} # payload
				}
				self.dispatch(message, Direction.InferDirection)
		
		self.displays.exit()


	def inferDirection(self, message):
		if message["type"] == "display":
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

	def dispatch(self, message, direction):

		if self.validateMessage(message) != 0:
			print(" [x] Dropping invalid message")
			return

		if direction == Direction.InferDirection:
			direction = self.inferDirection(message)

		if direction == Direction.ToDisplays:
			self.displays.process_message(message)
		else:
			print(" [x] Invalid message or destination. No information to route it!")

if __name__ == "__main__":
	poweroff = PowerOffApp()
	poweroff.run()

