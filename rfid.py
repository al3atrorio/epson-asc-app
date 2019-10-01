import serial
import time
from threading import Thread
from misc import Direction

class Rfid:
    def __init__(self, dispatcher):

        self.dispatcher = dispatcher

        self.serial_rfid1 = serial.Serial("/dev/ttyS5", 115200)
        self.serial_rfid1.flushInput()
        self.serial_rfid1.flushOutput()

        self.serial_rfid2 = serial.Serial("/dev/ttyS6", 115200)
        self.serial_rfid2.flushInput()
        self.serial_rfid2.flushOutput()

        self.serial_rfid3 = serial.Serial("/dev/ttyS4", 115200)
        self.serial_rfid3.flushInput()
        self.serial_rfid3.flushOutput()

        self.rfid1_thread = Thread(target = self.read_rfid1_thread)
        self.rfid1_thread.start()

        self.rfid2_thread = Thread(target = self.read_rfid2_thread)
        self.rfid2_thread.start()

        self.rfid3_thread = Thread(target = self.read_rfid3_thread)
        self.rfid3_thread.start()

    def read_rfid1_thread(self):
        while 1:
            try:
                code = self.serial_rfid1.readline().decode("utf-8").strip()
            except:
                print(" [x] Could not decode Rfid code on port 1")

            self.dispatch(code, "rfid1")
            time.sleep(0.01)
    
    def read_rfid2_thread(self):
        while 1:
            try:
                code = self.serial_rfid2.readline().decode("utf-8").strip()
            except:
                print(" [x] Could not decode Rfid code on port 2")

            self.dispatch(code, "rfid2")
            time.sleep(0.01)

    def read_rfid3_thread(self):
        while 1:
            try:
                code = self.serial_rfid3.readline().decode("utf-8").strip()
            except:
                print(" [x] Could not decode Rfid code on port 3")

            self.dispatch(code, "rfid3")
            time.sleep(0.01)
    
    def dispatch(self, code, connection):
        #Extracting Antena from the code
        #The code format is (a)xxxxxxxxxxxxx
        antenna = code[1]
        rfidCode = code[3:]

        #schedule message
        message = {
            "type": "rfid",
            "connection": connection,
            "payload": {
                "value": rfidCode,
                "antenna": antenna
            }
        }

        self.dispatcher(message, Direction.ToDojot)
