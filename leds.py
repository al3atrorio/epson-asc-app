import os
import re
import sched
import time
from threading import Thread

class Leds:
    def __init__(self):
        self.NUM_PORTS = 3
        self.LED_NAMES = [f"led{i+1}" for i in range(self.NUM_PORTS)] # ["led1", "led2", "led3"]
        self.COLOR_DICT = {
            "off"       : "#000000",
            # The definition below came from HTML 4.01 web colors
            "white"     : "#FFFFFF",
            "silver"    : "#C0C0C0",
            "gray"      : "#808080",
            "black"     : "#000000",
            "red"       : "#FF0000",
            "maroon"    : "#800000",
            "yellow"    : "#FFFF00",
            "olive"     : "#808000",
            "lime"      : "#00FF00",
            "green"     : "#008000",
            "aqua"      : "#00FFFF",
            "teal"      : "#008080",
            "blue"      : "#0000FF",
            "navy"      : "#000080",
            "fuchsia"   : "#FF00FF",
            "purple"    : "#800080"
        }

        self._sysfs_gpio = "/sys/class/gpio/"
        self._map_led_gpio = [
            {"r": "pioD5" , "g": "pioA26", "b": "pioD6"  },
            {"r": "pioA22", "g": "pioA25", "b": "pioA23" },
            {"r": "pioA20", "g": "pioA24", "b": "pioA21" }
        ]
        self._init_hw()

        # the variable below holds each led state (r, g, b), plus a blink parameter
        self._ledstate = [[0, 0, 0, "off"] for _ in range(self.NUM_PORTS)]

        # Thread to turn the led off after a programable delay
        # It contains a scheduler to wake up after the programable delay
        self._scheduler = sched.scheduler(time.time, time.sleep)
        self._sched_event_array = [[sched.Event(None, None, None, None, None)] for _ in range(self.NUM_PORTS)]
        self._thread_led_delay = Thread(target = self._sched_led_delay)
        self._thread_led_delay.start()

        # Thread to control the led delay (turn it off)
        self._thread_led_controller = Thread(target = self._thread_func_led_controller)
        self._thread_led_controller.start()


    def _init_hw(self):
        ''' This function inits the HW. It sets the gpio through sysfs '''
        for i in self._map_led_gpio:
            for pin in i.values():
                self._echo("0", self._sysfs_gpio + pin + "/value")
                self._echo("out", self._sysfs_gpio + pin + "/direction")
        '''
        The code below is used to set the PWM. The PWM is intended to
        a second step in this code development, so it's commented out

        self.pwm0 = "/sys/class/pwm/pwmchip0/pwm0/"
        self.pwm1 = "/sys/class/pwm/pwmchip0/pwm1/"
        self.gpio76 = "/sys/class/gpio/pioC12/"

        self.period0 = os.open(self.pwm0 + "period", os.O_RDWR)
        self.duty_cycle0 = os.open(self.pwm0 + "duty_cycle", os.O_RDWR)
        self.enable0 = os.open(self.pwm0 + "enable", os.O_RDWR)

        self.period1 = os.open(self.pwm1 + "period", os.O_RDWR)
        self.duty_cycle1 = os.open(self.pwm1 + "duty_cycle", os.O_RDWR)
        self.enable1 = os.open(self.pwm1 + "enable", os.O_RDWR)

        self.g = os.open(self.gpio76 + "value", os.O_RDWR)

        os.write(self.g,bytes("0", 'utf-8'))

        os.write(self.enable0,bytes("0", 'utf-8'))
        os.write(self.duty_cycle0,bytes(str("0"), 'utf-8'))
        os.write(self.enable1,bytes("0", 'utf-8'))
        os.write(self.duty_cycle1,bytes(str("0"), 'utf-8'))

        self.set(0, "off")
        '''


    def process_message(self, message):
        if "connection" not in message:
            print(" [*] Invalid LED strip message. No port!")
            return
        else:
            if message["connection"] in self.LED_NAMES:
                port = self.LED_NAMES.index(message["connection"])
            else:
                print(f" [x] Invalid LEDs Port Number!")
                return

        if "payload" not in message:
            print(" [*] Invalid LED strip message. No payload!")
            return
        payload = message["payload"]
        if "color" not in payload:
            print(" [*] Invalid LED strip message. No color!")
            return
        color = payload["color"]

        blink = payload["blink"] if ("blink" in payload) else "off"

        if self._sched_event_array[port] in self._scheduler.queue:
            # There is an led_off event scheduled in this port. Cancel it.
            self._scheduler.cancel(self._sched_event_array[port])

        # Now we check if there is a delay and schedule it.
        if "delay" in payload:
            delay = int(payload["delay"])
            if delay > 0:
                # schedule a LEDs off operation and store its reference
                self._sched_event_array[port] = self._schedule_leds_off(port, delay)

        # Set the led strip color
        self._set(port, color, blink)


    def _echo(self, text, filename):
        ''' This function is a short way to print to a file
            echo 1 > /sys/class/gpio/pioA20/value    (bash)
            ==
            echo("1", "/sys/class/gpio/pioA20/value")  (python) '''
        f = os.open(filename, os.O_RDWR)
        os.write(f, bytes(text, "utf-8"))
        os.close(f)


    def _set(self, port, color, blink="off"):
        ''' Set the led strip color.
            port is a numeric value from 0 to (self.NUM_PORTS-1)
            color is a string with a color from self.COLOR_DICT or
                  a #RRGGBB representation, similar to the HTML standards '''
        # Convert the color string to a ##RRGGBB representation
        color = color.lower()
        if color in self.COLOR_DICT:
            # Convert the color acording to the color dictionary
            color = self.COLOR_DICT[color]
        elif re.match("#[A-Za-z0-9]{3}", color):
            # Double the chars to convert from #RGB to a #RRGGBB representation
            color = "#" + "".join([x*2 for x in color[1:]])

        # Extract the tuple r, g, b (as integers) from color if possible. Otherwise, zero
        if re.match("#[A-Za-z0-9]{6}", color):
            (r, g, b) = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        else:
            # If I can't find a color, then turn the LEDs off
            (r, g, b) = (0, 0, 0)

        # Currently, I set the LEDs to either on of off
        r_bool = 1 if r >= 128 else 0
        g_bool = 1 if g >= 128 else 0
        b_bool = 1 if b >= 128 else 0
        self._ledstate[port] = [r_bool, g_bool, b_bool, blink]
        # Note: The actual LED programming is done by _led_controller


    def _schedule_leds_off(self, port, delay):
        ''' This function schedules the port to turn the leds of after delay seconds '''
        ''' it returns the event code, so it can be canceled by further commands     '''
        # The priority of the event in the scheduler is 9, #because_reasons
        return self._scheduler.enter(delay, 9, self._set, (port, "off", "off"))


    def _sched_led_delay(self):
        ''' This function runs in a different thread because the scheduler 
            usually depends on a backgroud thread, like this one           '''
        while True:
            self._scheduler.run()
            time.sleep(0.01)


    def do_every(self, period, f, *args):
        ''' This function was copied from Stackoverflow and
            it runs the function f periodically                 '''
        def g_tick():
            t = time.time()
            count = 0
            while True:
                count += 1
                yield max(t + count*period - time.time(),0)
        g = g_tick()
        while True:
            time.sleep(next(g))
            f(*args)


    def _thread_func_led_controller(self):
        ''' This function runs in a thread and programs _led_controller()
            to run periodically                                             '''
        self.do_every(0.1, self._led_controller)


    def _led_controller(self, *unused_args):
        ''' This function does the actual LED control.
            It reads _ledstate and then commands the GPIOs.
            It runs at 0.1s intervals, so it can control the LEDs
            blinking.                                                  '''
        for port in range(self.NUM_PORTS):
            # in non-blinking situations, _ledgpio will follow the _ledstate
            self._led_controller._ledgpio[port] = self._ledstate[port][0:3]

            # turn the leds off if in blink state and in off time
            if ((self._ledstate[port][3] == "blink_fast")
                    and (self._led_controller_count % 2 == 1)):
                self._led_controller._ledgpio[port] = [0, 0, 0]
            elif ((self._ledstate[port][3] == "blink_slow")
                    and (self._led_controller_count >= 5)):
                self._led_controller._ledgpio[port] = [0, 0, 0]

            # send command to GPIO if the previous state is different from the intended state
            for led_n, led_c in enumerate(['r', 'g', 'b']):
                if self._led_controller._ledgpio[port][led_n] != self._led_controller._ledgpio_old[port][led_n]:
                    gpio_file = self._sysfs_gpio + self._map_led_gpio[port][led_c] + "/value"
                    self._echo(str(self._led_controller._ledgpio[port][led_n]), gpio_file)
                    self._led_controller._ledgpio_old[port][led_n] = self._led_controller._ledgpio[port][led_n]
        self._led_controller_count = (self._led_controller_count + 1) % 10
    # The variables below simulate static variables for the method _led_controller()
    _led_controller._ledgpio = [[0 for _ in ['r', 'g', 'b']] for _ in range(3)]
    _led_controller._ledgpio_old = [[0 for _ in ['r', 'g', 'b']] for _ in range(3)]
    _led_controller_count = 0  # I can't use _led_controller.count because it throws an error
