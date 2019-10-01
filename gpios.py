import os
import sched
import time
from threading import Thread
import gpio_client
from misc import Direction

class Gpios:
    def __init__(self, dispatcher):        

        self.dispatcher = dispatcher
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.connection_numbers_out = {f"gpio_out{i}":i for i in [1,2,3,4,5,6]}
        self._thread = Thread(target = self._sched_thread)
        self._thread.start()

        gpio_client.init_gpio_client(self.callback)

    def schedule(self, delay, priority, func, args):
        self.scheduler.enter(delay, priority, func, args)
	
    def _sched_thread(self):
        while 1:
            self.scheduler.run()
            time.sleep(0.03)

    def validate_message(self, message):
        if "payload" not in message:
            print(" [x] Gpio message has no payload.")
            return 1
        
        payload = message["payload"]

        if "connection" not in message:
            print(" [x] Gpio message has no connection.")
            return 1
        
        if message["connection"] not in self.connection_numbers_out:
            print(" [x] Invalid Port. Discarding Gpio message!")
            return 1

        port = self.connection_numbers_out[message["connection"]]

        if port < 1 or port > 6:
            print(" [x] Invalid Port number. Discarding Gpio message!")
            return 1
        
        if "value" not in payload:
            print(" [x] Gpio message has no value.")
            return 1
        
        if "delay" in payload:
            delay = int(payload["delay"])
            if delay < 0:
                print(" [x] Invalid delay in Gpio message")
                return 1
        
        return 0

    def process_message(self, message):
        if self.validate_message(message):
            print(" [x] Invalid Gpio message. Discarding!")

        payload = message["payload"]
        port = self.connection_numbers_out[message["connection"]] -1 #The driver uses the por starting at 0
        value = 1 if payload["value"] == "on" else 0

        self.set(port, value)

        #Now we check if there is a delay and schedule it.
        if "delay" in payload:
            delay = int(payload["delay"])

            if delay > 0:
                value_after_delay = 1 if value == 0 else 0
                self.schedule(delay, 9, self.set, (port, value_after_delay))

    def set(self, port, value):
        gpio_client.write_gpio(port, value)
    
    def callback(self, port, value):
        print(" [*] Callback received in Python")
        print(" [*] Gpio value received from driver: " + str(value))

        #schedule message
        message = {
            "type": "gpio",
            "connection": f"gpio_in{port+1}", #+1 because the driver starts at 0
            "payload": {
                "value": "on" if value == 1 else "off"
            }
        }

        self.dispatcher(message, Direction.ToDojot)
