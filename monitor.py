import socket, struct, fcntl
from threading import Thread
import time
from misc import Direction

class Monitor:
    def __init__(self, dispatcher, config):
        self.dispatcher = dispatcher
        self.config = config

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sockfd = self.sock.fileno()
        self.SIOCGIFADDR = 0x8915

        self.ip = "Nenhum"
        self.wifi_ip = "Nenhum"

        self.rfids = "RFID: "

        self.version = self.config.version

        if self.config.wifi_enabled == "yes":
            self.wifi_status = "Wifi ON. Sem conexão."
        else:
            self.wifi_status = "Wifi não ativo."

        if self.config.web_enabled:
            self.web_status = "Web ON."
        else:
            self.web_status = "Web OFF"

        for i in self.config.rfids:
            self.rfids += "N" if i == 1 else "S"

        self.update()

        self.monitor_thread = Thread(target = self.monitoring_thread)
        self.monitor_thread.start()

    def get_ip(self, iface = 'br0'):
        ifreq = struct.pack('16sH14s', iface.encode('utf-8'), socket.AF_INET, b'\x00'*14)
        try:
            res = fcntl.ioctl(self.sockfd, self.SIOCGIFADDR, ifreq)
        except:
            return "Nenhum"
        ip = struct.unpack('16sH2x4s8x', res)[2]
        return socket.inet_ntoa(ip)

    def monitoring_thread(self):
        while 1:
            current_ip = self.get_ip("br0")            
            if current_ip != self.ip:
                self.ip = current_ip
                self.update()

            current_wifi_ip = self.get_ip("wlan0")
            if current_wifi_ip != self.wifi_ip:
                self.wifi_ip = current_wifi_ip
                if current_wifi_ip == "Nenhum":
                    self.wifi_status = "Wifi ON. Sem conexão."
                else:
                    self.wifi_status = f"Wifi: {self.wifi_ip}"
                self.update()

            time.sleep(3)

    def update(self):
        for i in range(3):
            message = {
                "type": "display",
                "connection": f"display{i+1}",
                "payload": {
                    "screen4": {
                        "line4": {
                            "text": f"IP: {self.ip}",
                            "inverted": True
                        },
                        "line5": {
                            "text": f"{self.wifi_status}",
                            "inverted": True
                        },
                        "line6": {
                            "text": f"{self.web_status} - {self.rfids}",
                            "inverted": True
                        },
                        "line7": {
                            "text": f"{self.config.mac}",
                            "inverted": True
                        },
                        "line8": {
                            "text": f"{self.version}",
                            "inverted": True
                        }
                    }
                }
            }
            self.dispatcher(message, Direction.ToDisplays, save=False)
