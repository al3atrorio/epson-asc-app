import os
import datetime
import time
from threading import Thread
from collections import deque
from misc import Direction
import json

class State:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.buffer = deque(maxlen=128)
        self.state = {}
        self.stateFile = None
        self.enable = self.checkSdCardPresence()
        self.enableDateCheck = False #always false in this version

        self.state["display"] = {
                "display1": {
                    "type": "display", "connection": "display1",
                    "payload": {
                        "screen1": {}, "screen2": {}, "screen3": {}, "screen4": {},
                        "leds": {}, "backlight": {}, "sound": {}, "icons": {},
                    }
                },
                "display2": {
                    "type": "display", "connection": "display2",
                    "payload": {
                        "screen1": {}, "screen2": {}, "screen3": {}, "screen4": {},
                        "leds": {}, "backlight": {}, "sound": {}, "icons": {},
                    }
                },
                "display3": {
                    "type": "display", "connection": "display3",
                    "payload": {
                        "screen1": {}, "screen2": {}, "screen3": {}, "screen4": {},
                        "leds": {}, "backlight": {}, "sound": {}, "icons": {},
                    }
                },
            } 
        self.state["gpio"] = {}
        self.state["led"] = {}

        if self.enable and self.thereIsStateToLoad():
            self.loadState()

        if self.enable:
            self._thread = Thread(target = self.stateThread)
            self._thread.start()
    
    def checkSdCardPresence(self):
        if os.path.exists("/dev/mmcblk0p1"):
            print(" [*] Sd card present.")
            return True
        else:
            print(" [*] Sd card NOT present. Save State disabled.")
            return False

        return False

    def openStateFile(self):
        try:
            self.stateFile = open("/media/state.json", "w+")
        except Exception as e:
            print(e)
            self.enable = False
    
    def thereIsStateToLoad(self):
        if os.path.isfile("/media/state.json"):
            if os.path.getsize("/media/state.json") > 0:
                print(" [*] There is state to load")
                return True
        
        print(" [*] No state to load")
        return False
    
    def loadState(self):
        try:
            stateFile = open("/media/state.json", "r")
            config = json.load(stateFile)
            stateFile.close()
            #print(config)

            self.state = config

            if self.enableDateCheck == True:
                if "date" in config:
                    configDate = datetime.datetime.strptime(config["date"], '%Y-%m-%d %H:%M:%S.%f')
                    timePassed = datetime.datetime.now() - configDate

                    if c.total_seconds() < 5*60:
                        print(" [*] The state will be loaded. Hard reboot detected less than 5 minutes ago.")
                    else:
                        print(" [*] The state won't be loaded. Hard reboot detected more than 5 minutes ago.")
                        return

            if "display1" in config["display"]:
                self.dispatcher(config["display"]["display1"], Direction.ToDisplays, save=False)
                print(" [*] Loading Display 1 state")
            if "display2" in config["display"]:
                self.dispatcher(config["display"]["display2"], Direction.ToDisplays, save=False)       
                print(" [*] Loading Display 1 state")
            if "display3" in config["display"]:
                self.dispatcher(config["display"]["display3"], Direction.ToDisplays, save=False)
                print(" [*] Loading Display 1 state")
            if "gpio1" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio1"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 1 state")
            if "gpio2" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio2"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 2 state")
            if "gpio3" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio3"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 3 state")
            if "gpio4" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio4"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 4 state")
            if "gpio5" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio5"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 5 state")
            if "gpio6" in config["gpio"]:
                self.dispatcher(config["gpio"]["gpio6"], Direction.ToGpios, save=False)
                print(" [*] Loading Gpio 6 state")
            if "led1" in config["led"]:
                self.dispatcher(config["led"]["led1"], Direction.ToLeds, save=False)
                print(" [*] Loading Led 1 state")
            if "led2" in config["led"]:
                self.dispatcher(config["led"]["led2"], Direction.ToLeds, save=False)
                print(" [*] Loading Led 2 state")
            if "led3" in config["led"]:
                self.dispatcher(config["led"]["led3"], Direction.ToLeds, save=False)
                print(" [*] Loading Led 3 state")
        
        except Exception as e:
            print(e)
            print(" [x] Could not load the saved State")

    def stateThread(self):
        save = False

        while 1:
            while len(self.buffer) > 0:
                message = self.buffer.popleft()

                self.state["date"] = str(datetime.datetime.now())

                if "type" in message:
                    if message["type"] == "display":
                        self.saveDisplay(message)
                        save = True
                    elif message["type"] == "gpio":
                        self.saveGpio(message)
                        save = True
                    elif message["type"] == "led":
                        self.saveLed(message)
                        save = True

            if save:
                self.writeStateToFile()
                save = False
                
            time.sleep(0.5)
    
    def saveLed(self, message):
        if message["connection"] == "led1":
            self.state["led"]["led1"] = message
        elif message["connection"] == "led2":
            self.state["led"]["led2"] = message
        elif message["connection"] == "led3":
            self.state["led"]["led3"] = message

    def saveDisplay(self, message):
        disp_name =  message["connection"]

        self.state["display"][disp_name]["type"] = "display"
        self.state["display"][disp_name]["connection"] = disp_name
        if "screen1" in message["payload"]: self.state["display"][disp_name]["payload"]["screen1"].update(message["payload"]["screen1"])
        if "screen2" in message["payload"]: self.state["display"][disp_name]["payload"]["screen2"].update(message["payload"]["screen2"])
        if "screen3" in message["payload"]: self.state["display"][disp_name]["payload"]["screen3"].update(message["payload"]["screen3"])
        if "screen4" in message["payload"]: self.state["display"][disp_name]["payload"]["screen4"].update(message["payload"]["screen4"])
        if "icons" in message["payload"]: self.state["display"][disp_name]["payload"]["icons"].update(message["payload"]["icons"])
        if "leds" in message["payload"]: self.state["display"][disp_name]["payload"]["leds"].update(message["payload"]["leds"])
        if "backlight" in message["payload"]: self.state["display"][disp_name]["payload"]["backlight"].update(message["payload"]["backlight"])
        if "sound" in message["payload"]: self.state["display"][disp_name]["payload"]["sound"].update(message["payload"]["sound"])

    def saveGpio(self, message):
        if message["connection"] == "gpio1":
            self.state["gpio"]["gpio1"] = message
        elif message["connection"] == "gpio2":
            self.state["gpio"]["gpio2"] = message
        elif message["connection"] == "gpio3":
            self.state["gpio"]["gpio3"] = message
        elif message["connection"] == "gpio4":
            self.state["gpio"]["gpio4"] = message
        elif message["connection"] == "gpio5":
            self.state["gpio"]["gpio5"] = message
        elif message["connection"] == "gpio6":
            self.state["gpio"]["gpio6"] = message
        
    def writeStateToFile(self):
        try:
            stateFile = open("/media/state.json", "w+")
            stateFile.truncate(0)
            stateFile.write(json.dumps(self.state))
            stateFile.close()
        except Exception as e:
            print(e)
            print(" [x] Error writing to State file!")

    def saveState(self, message):
        self.buffer.append(message)