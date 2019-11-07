import pymodbus
import serial
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import serial.rs485
import time
from collections import deque
from threading import Thread
from misc import Direction

class Displays:
    def __init__(self, dispatcher, reset=1):
        print("Starting Displays")

        self.active = True
        self.dispatcher = dispatcher
        self.auto_reset = reset

        self.last_accessed_unit = 0

        self.MAX_DISPLAY = 3
        self.DISP_NAMES = [f"display{i+1}" for i in range(self.MAX_DISPLAY)] # ["display1", "display2", "display3"]
        self.REG_ADDR = {
            "small": {
                "ID"            : 0,
                "ALERT"         : 4,
                "TEXT_BASE"     : 0,
                "ICON_EN_BASE"  : 96,
                "CLEAR_SCR"     : 97,
                "LED_BASE"      : 400,
                "BACKLIGHT"     : 406,
                "ICON_BASE"     : 407,
                "ICON_FORMAT"   : 415,
                "SOUND"         : 416,
                "ATTEND"        : 417,
                "ACCESS"        : 420,
                "RESET"         : 429
            },
            "big" : {
                "ID"            : 0,
                "ALERT"         : 4,
                "TEXT_BASE"     : 0,
                "ICON_EN_BASE"  : 336,
                "CLEAR_SCR"     : 337,
                "LED_BASE"      : 1360,
                "BACKLIGHT"     : 1366,
                "ICON_BASE"     : 1367,
                "ICON_FORMAT"   : 1382,
                "SOUND"         : 1383,
                "ATTEND"        : 1384,
                "ACCESS"        : 1385,
                "RESET"         : 1389
            }
        }
        self.DISPLAY_PARAMS = {
            "small": {
                "max_line"              : 8,
                "max_col"               : 21,
                "max_led"               : 6,
                "max_icon"              : 8,
                "max_screen"            : 4,
                "max_screen_word"       : 100,
                "max_backlight_timer"   : 254,
                "max_sound_timer"       : 15,
                "max_sound_repetition"  : 255,
                "sleep_after_clear_screen"  : 0.1
            },
            "big": {
                "max_line"              : 16,
                "max_col"               : 40,
                "max_led"               : 6,
                "max_icon"              : 16,
                "max_screen"            : 4,
                "max_screen_word"       : 340,
                "max_backlight_timer"   : 254,
                "max_sound_timer"       : 15,
                "max_sound_repetition"  : 255,
                "sleep_after_clear_screen"  : 0.3
            }
        }

        self.buffer = deque(maxlen=128)
        self.connection = self.init_rs485_connection()
        self.display_types = [None, None, None]
        self.multiplier_to_check_connections = 0

        self.disp_thread = Thread(target = self.displays_thread)
        self.disp_thread.daemon = True # This makes the thread to exit when the program ends
        self.disp_thread.start()


    def exit(self):
        self.active = False
        self.disp_thread.join()


    def get_display_types(self):
        return self.display_types


    def reset_display(self, display):
        print(f"Reseting - {display}")

        if display == "display1":
            self.write_registers(i, "RESET", 0x1248)
        elif display == "display2":
            self.write_registers(i, "RESET", 0x1248)
        elif display == "display3":
            self.write_registers(i, "RESET", 0x1248)
        

    def sleep(self, display):
        print(f"Sleeping - {display}")

        if display == "display1":
            self.write_registers(0, "RESET", 0x1249)
        elif display == "display2":
            self.write_registers(1, "RESET", 0x1249)
        elif display == "display3":
            self.write_registers(2, "RESET", 0x1249)


    def show_init_message(self):
        for i in range(3):
            message = {
                "type": "display",
                "connection": f"display{i+1}",
                "payload": {
                    "screen1": {
                        "options": {
                            "clear_screen": True
                        }
                    },
                    "icons": {
                        "screen1_status": "off",
                        "screen2_status": "off",
                        "screen3_status": "off",
                        "screen4_status": "off"
                    },
                    "backlight": {
                        "value": "on",
                    }, # backlight
                }
            }
            self.buffer.append(message)


    def is_in_num_range(self, value, min, max):
        """
        This function check if a variable is inside a numeric range,
        including the min and max values.
        I needed this function because it's possible that the variable
        is not a number
        """
        try:
            if min <= value <= max:
                return True
            return False
        except:
            return False


    def init_rs485_connection(self):
        client = ModbusClient(method='rtu', port='/dev/ttyS3', rtscts=True, stopbits = 1, bytesize = 8, baudrate = 115200, timeout=0.1, parity = 'N')
        client.connect()
        rs485_mode = serial.rs485.RS485Settings(delay_before_tx = 0, delay_before_rx = 0, rts_level_for_tx=True, rts_level_for_rx=False, loopback=False)
        client.socket.rs485_mode = rs485_mode

        return client

    
    def update_connected_displays(self):

        current_types = self.display_types.copy()

        #Get the types
        for i in range(3):
            try:
                # We can't use self.read_register() to read the ID
                # address (address 0) because we still don't know
                # the display type.
                response = self.connection.read_input_registers(0x00,1,unit=i+1)
                
                if response.isError():
                    current_types[i] = None
                elif response.registers[0] == 0xa0a1:
                    current_types[i] = "small"
                elif response.registers[0] == 0xa0a2:
                    current_types[i] = "big"
            except Exception as e:
                print(e)
                #If there is a error while reading, the type remains the same for
                #that display untill the next check
                pass
           
            time.sleep(0.1)

        for i in range(3):
            if current_types[i] != self.display_types[i]:
                print(f" [*] Display on port {i+1} is {current_types[i]}")

                self.display_types[i] = current_types[i]

                #We reset when a new display is pluged in. 
                if current_types[i] != None and self.auto_reset == 1:
                    self.write_registers(i, "RESET", 0x1248)
        
    
    def displays_thread(self):
        print(" [*] Display Thread Starting")
        self.update_connected_displays()

        #When the application starts we need to wait for the displays
        #to reset before sendind the initial messages.
        time.sleep(9) 

        #self.show_init_message()

        start = time.time()

        while self.active:

            if (time.time() - start) > 0.5:
                self.check_alert()
                start = time.time()
                
                #After 10*0.5s=5s we check the ports to see if something changed.
                #This way we can dinamically change the ports.
                #We are disabling this feature because it's not 100% stable.
                #self.multiplier_to_check_connections += 1
                #if self.multiplier_to_check_connections % 10 == 0:
                #    self.update_connected_displays()
                #    self.multiplier_to_check_connections = 0

            while len(self.buffer) > 0:
                message = self.buffer.popleft()
                self.send_message_to_display(message)
            time.sleep(0.01)

    def check_alert(self):
        for i in range(self.MAX_DISPLAY):
            if self.display_types[i] != None:
                try:
                    response = self.read_register(i, "ALERT")
                    if response != None:
                        if response != 0:
                            self.send_alert(f"display{i+1}")
                            self.write_registers(i, "ATTEND", 0x1)
                except Exception as e:
                    print(e)
                    print(f" [x] Error on getting alert on Display {i+1}")
        

    def send_alert(self, port):
        print(f"Alert on {port}!")

        message = {
            "type": "alert",
            "connection": f"{port}-button",
            "payload": {}
        }

        self.dispatcher(message, Direction.ToDojot)
    
    def send_message_to_display(self, message):
        # Identify the display number from the message
        if message["connection"] in self.DISP_NAMES:
            display = self.DISP_NAMES.index(message["connection"])
        else:
            if message["connection"] in [str(i+1) for i in range(self.MAX_DISPLAY)]:
                print(f" [x] Warning: Using deprecated connection value")
                display = int(message["connection"]) - 1
            else:
                print(f" [x] Invalid Display Port Number!")
                return

        if self.display_types[display] in ["small", "big"]:
            self.route_message(display, message)
        else:
            print(f" [x] No display connected on port {display + 1}! Message discarted...")

    def process_message(self, message):
        ''' This method is the one that receives messages from application.py.
            It is the entry point to everything in this class.
        '''
        self.buffer.append(message)


    def read_register(self, display, reg_name):
        ''' Read the value in the display's register
            display is an int in range(self.MAX_DISPLAY), starting in 0
            reg_name is a string defined in self.REG_ADDR
            return an int or None in case of error

            The function uses the display type ("big" or "small") and
            self.REG_ADDR to discover the numeric address
        '''

        if self.last_accessed_unit != display:
            self.last_accessed_unit = display
            time.sleep(0.05)

        if ((self.display_types[display] in self.REG_ADDR) and
                (reg_name in self.REG_ADDR[self.display_types[display]])):
            register = self.REG_ADDR[self.display_types[display]][reg_name]
            try:
                response = self.connection.read_input_registers(register, 1, unit=display+1)
                if response.isError():
                    return None
                else:
                    return response.registers[0]
            except:
                return None
        else:
            print(f" [x] Coding error in display.read_register({display}, {reg_name}")
            print(f"     display_types[display] = {display_types[display]}")
            return None


    def write_registers(self, display, reg_name, values, offset=0):
        ''' Write the value in the display's register
            display is an int in range(self.MAX_DISPLAY), starting in 0
            reg_name is a string defined in self.REG_ADDR
            values is either an int value or a list of values

            The function uses the display type ("big" or "small") and
            self.REG_ADDR to discover the numeric address.
            If values is a single value, write_register is called.
            If values is a list of ints, write_registers is called.
        '''

        if self.last_accessed_unit != display:
            self.last_accessed_unit = display
            time.sleep(0.05)

        # TODO: Check parameters
        try:
            register = self.REG_ADDR[self.display_types[display]][reg_name] + offset
            if isinstance(values, list):
                # Write a list of values
                rq = self.connection.write_registers(register, values, unit=display+1)
            else:
                # Write a single value
                rq = self.connection.write_register(register, values, unit=display+1)

        except:
            print(f" [x] Error while trying to write register {reg_name} wuth offset={offset} in display {display}+1")


    def set_lines(self, display, screen, screen_data):
        if "options" in screen_data:
            if "clear_screen" in screen_data["options"]:
                if screen_data["options"]["clear_screen"] == True:
                    self.clean_screen(display, screen)

        for l in range(self.DISPLAY_PARAMS[self.display_types[display]]["max_line"]):
            line_name = "line" + str(l+1)
            if line_name in screen_data:
                self.write_line(display, screen, l, screen_data[line_name])


    def write_line(self, display, screen, line_number, line_data):
        max_screen_word = self.DISPLAY_PARAMS[self.display_types[display]]["max_screen_word"]
        max_col = self.DISPLAY_PARAMS[self.display_types[display]]["max_col"]
        # max_col must be an odd number because the registers have 16 bits
        if max_col % 2 != 0:
            max_col += 1

        line_string = line_data["text"][:max_col] # Extract up to max_col chars
        line_string = line_string.ljust(max_col) # If string is short, pad it with spaces

        data = line_string.encode('latin-1')
        
        coded_string = [data[i]*16**2 + data[i+1] for i in range(0,len(data),2)]

        mod = 0x0000
        if "inverted" in line_data:
            if line_data["inverted"] == True:
                mod = mod | (1<<0)
        
        if "blink" in line_data:
            if line_data["blink"] == True:
                mod = mod | (1<<1)

        if "double_size" in line_data:
            if line_data["double_size"] == True:
                mod = mod | (1<<2)

        max_col_word = max_col//2 # There are two chars by word
        self.write_registers(display, "TEXT_BASE", mod,
                offset=(screen*max_screen_word + (max_col_word+1)*line_number + max_col_word))
        rq = self.write_registers(display, "TEXT_BASE", coded_string,
                offset=(screen*max_screen_word + (max_col_word+1)*line_number))


    def clean_screen(self, display, screen):
        max_screen_word = self.DISPLAY_PARAMS[self.display_types[display]]["max_screen_word"]
        self.write_registers(display, "CLEAR_SCR", 0x0001, offset=screen*max_screen_word)
        time.sleep(self.DISPLAY_PARAMS[self.display_types[display]]["sleep_after_clear_screen"])


    def set_sound(self, display, sound_data):
        max_timer = self.DISPLAY_PARAMS[self.display_types[display]]["max_sound_timer"]
        max_repeat = self.DISPLAY_PARAMS[self.display_types[display]]["max_sound_repetition"]
        if (("reps" in sound_data) and ("active_time" in sound_data)) and ("inactive_time" in sound_data):
            reps = sound_data["reps"]
            active_time =sound_data["active_time"]
            inactive_time =sound_data["inactive_time"]
            if (self.is_in_num_range(reps, 0, max_repeat)
                    and self.is_in_num_range(inactive_time, 0, max_timer)
                    and self.is_in_num_range(active_time, 0, max_timer)):
                data = (reps << 8) | (inactive_time << 4) | (active_time)
                self.write_registers(display, "SOUND", data)
            else:
                print(f" [x] Invalid display sound data: reps={reps}, active_time={active_time}, inactive_time={inactive_time}")
        else:
            print(" [x] Invalid display sound request, required parameters not present")



    def set_backlight(self, display, backlight_data):
        BACKLIGHT_STATUS_DICT = {
            "on"            : 0,
            "off"           : 1,
            "slow_blink"    : 2,
            "fast_blink"    : 3
        }
        max_timer = self.DISPLAY_PARAMS[self.display_types[display]]["max_backlight_timer"]
        if (("value" in backlight_data)
                and (backlight_data["value"] in BACKLIGHT_STATUS_DICT)):
            data = BACKLIGHT_STATUS_DICT[backlight_data["value"]]
            # if timer isn't defined, then use infinite
            # if the timer is defined, but not ok, use 0
            # if timer is defined and ok, use the timer
            if ("timer" not in backlight_data):
                timer = max_timer + 1
            else:
                timer = backlight_data["timer"]
                if not self.is_in_num_range(timer, 0, max_timer):
                    timer = 0
                    print(f" [x] Invalid display backlight timer: {timer}")
            if timer > 0:
                data |= (timer << 8)
                self.write_registers(display, "BACKLIGHT", data)
        else:
            print(" [x] Invalid display backlight request, required parameter 'value' not present or incorrect")


    def set_leds(self, display, led_data):
        LED_STATUS_DICT = {
            "on"            : 1,
            "off"           : 0,
            "slow_blink"    : 2,
            "fast_blink"    : 3
        }

        for i in range(self.DISPLAY_PARAMS[self.display_types[display]]["max_led"]):
            led_name = "led" + str(i+1)
            if led_name in led_data:
                if led_data[led_name]["value"] in LED_STATUS_DICT:
                    value = LED_STATUS_DICT[led_data[led_name]["value"]]
                    if "timer" in led_data[led_name]:
                        value = value | ((led_data[led_name]["timer"] & 0xff)<<8)
                    else:
                        value = value | 0xff00
                    self.write_registers(display, "LED_BASE", value, offset=i)


    def set_icons(self, display, icons_data):
        ICON_STATUS_DICT = {
            "on"        : 1,
            "off"       : 0
        }
        ICON_POSITION_DICT = {
            "left"      : 0,
            "right"     : 2,
            "top"       : 1,
            "bottom"    : 3
        }

        for i in range(self.DISPLAY_PARAMS[self.display_types[display]]["max_screen"]):
            screen_name = "screen" + str(i+1) + "_status"
            if screen_name in icons_data:
                if icons_data[screen_name] in ICON_STATUS_DICT:
                    value = ICON_STATUS_DICT[icons_data[screen_name]]
                    offset = i * self.DISPLAY_PARAMS[self.display_types[display]]["max_screen_word"]
                    self.write_registers(display, "ICON_EN_BASE", value, offset=offset)

        if "position" in icons_data:
            if icons_data["position"] in ICON_POSITION_DICT:
                value = ICON_POSITION_DICT[icons_data["position"]]
                self.write_registers(display, "ICON_FORMAT", value)

        for i in range(self.DISPLAY_PARAMS[self.display_types[display]]["max_icon"]):
            icon_name = "icon" + str(i+1)
            if icon_name in icons_data:
                value = icons_data[icon_name]["picture_number"]

                if "inverted" in icons_data[icon_name]:
                    if icons_data[icon_name]["inverted"] == True:
                        value = value | (1<<8)
                
                if "blink" in icons_data[icon_name]:
                    if icons_data[icon_name]["blink"] == True:
                        value = value | (1<<9)
                self.write_registers(display, "ICON_BASE", value, offset=i)


    def route_message(self, display, message):
        #TODO: colocar rotina de validação.
        if "payload" in message:
            payload = message["payload"]
        else: 
            print(" [x] Invalid display message. No payload!")

        if "lines" in payload:
            print(f" [*] Warning: Using deprecated payload \"lines\". Use \"screen1\" instead")
            self.set_lines(display, 0, payload["lines"])

        for s in range(self.DISPLAY_PARAMS[self.display_types[display]]["max_screen"]):
            if f"screen{s+1}" in payload:
                self.set_lines(display, s, payload[f"screen{s+1}"])

        if "sound" in payload:
            self.set_sound(display, payload["sound"])

        if "backlight" in payload:
            self.set_backlight(display, payload["backlight"])

        if "leds" in payload:
            self.set_leds(display, payload["leds"])

        if "icons" in payload:
            self.set_icons(display, payload["icons"])
