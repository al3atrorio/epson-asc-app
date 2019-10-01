import os
import urllib.request
import lwm2m_client
from threading import Thread
from time import sleep
import json
import subprocess
import asyncio
import aiocoap

class Lwm2m:
    def __init__(self, config):        
        self.state = "idle"
        self.nextstate = "idle"
        self.url = ""
        self.res = 0
        self.version = config.version

        self._thread = Thread(target = self.firmware_update_thread)
        self._thread.start()

    def firmware_update_thread(self):
        print(" [*] Firmware Update Thread Created.")

        while lwm2m_client.init_lwm2m_client(self.callback) != 0:
            print(" [*] Lwm2m client daemon not started. Waiting...")
            sleep(1)

        lwm2m_client.set_string_lwm2m("/5/0/6", self.version)
        lwm2m_client.set_string_lwm2m("/5/0/7", self.version)
        lwm2m_client.set_string_lwm2m("/3/0/3", self.version)
        lwm2m_client.set_integer_array_lwm2m("/5/0/8", 2)
        lwm2m_client.set_integer_lwm2m("/5/0/9", 0)

        #Check if there was an update and set the result in node /5/0/5
        if os.path.isfile("/tmp/update.json"):
            print(" [*] Lwm2m - The system was updated")

            with open("/tmp/update.json", "r") as config_file:
                self.config = json.load(config_file)

            if int(self.config["result"]) == 0:
                result = 1
                print(" [*] Lwm2m - Result 1")
            else:
                result = 8
                print(" [*] Lwm2m - Result 8")

            self.nextstate = "idle"
            lwm2m_client.set_integer_lwm2m("/5/0/3", 0)
            lwm2m_client.set_integer_lwm2m("/5/0/5", result)
        else:
            print(" [*] Lwm2m - There was no update in the last reboot!")

        while 1:
            sleep(1)

    def callback(self, data):

        if data[0] == 1 and data[1].decode('utf-8') == " ": 
            print(" [*] Empty URL - Reseting State Machine")
            self.nextstate = "idle"

            #Setting the result to 0 when reseting
            self.res = 0
            lwm2m_client.set_integer_lwm2m("/5/0/5", 0)

        while True:

            self.state = self.nextstate

            if self.state == "idle":
                print(" [*] State - idle state")

                lwm2m_client.set_integer_lwm2m("/5/0/3", 0)
                
                if data[0] == 1 and data[1].decode('utf-8') != " " and self.res == 0:                    
                    self.url = data[1].decode('utf-8')
                    print(" [*] The Firmware URL is: " + self.url)
                    lwm2m_client.set_integer_lwm2m("/5/0/5", 0)
                    self.nextstate = "downloading"

            elif self.state == "downloading":
                print(" [*] State - downloading state")

                lwm2m_client.set_integer_lwm2m("/5/0/3", 1)
                result = self.download_file(self.url)

                if result != 0:
                    self.nextstate = "idle"
                    self.res = 7
                    lwm2m_client.set_integer_lwm2m("/5/0/5", 7)
                else:
                    self.nextstate = "downloaded"
            
            elif self.state == "downloaded":
                print(" [*] State - downloaded state")

                lwm2m_client.set_integer_lwm2m("/5/0/3", 2)

                #if the command was an execute, change to updating state.
                #Otherwise wait for the execute.
                if data[0] == 2:
                    self.nextstate = "updating"
                    
            elif self.state == "updating":
                print(" [*] State - updating state")

                lwm2m_client.set_integer_lwm2m("/5/0/3", 3)

                print(" [*] Executando o Update")
                result = subprocess.call(['/root/app/update.sh'])
                print(" [*] Update executed. Result: " + str(result))

                if result == 0:
                    print(" [*] Update Flash OK! Rebooting")
                    os.system('reboot')
                else:
                    self.res = 5
                    print(f" [*] Error while updating. System NOT updated. Code: {self.res}")
                    lwm2m_client.set_integer_lwm2m("/5/0/5", self.res)
                    self.nextstate = "idle"

            if self.state == self.nextstate:
                break
    
    def download_file(self, url):
        print(' [*] Beginning file download...')

        if url.startswith("http"):
            return self.download_http(url)
        elif url.startswith("coap"):
            #return self.download_coap(url)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.download_coap(url))
            loop.close()
            return result
        else:
            print(f" [x] Update: Invalid Url: {url}")
            return 1
        
        return 1

    def download_http(self, url):
        print(' [*] Downloading using Http...')

        try:
            urllib.request.urlretrieve(url, '/tmp/update_downloaded.swu')  
            print(' [*] Download finished.')
            return 0
        except Exception as e:
            print(f" [*] Url not found!")
            return 1

        return 0

    async def download_coap(self, url):
        print(' [*] Downloading using Coap...')

        protocol = await aiocoap.Context.create_client_context()
        request = aiocoap.Message(code=aiocoap.GET, uri=url)

        try:
            response = await protocol.request(request).response
        except Exception as e:
            print(f" [x] Failed to fetch url: {url}")
            print(e)
            return 1
        else:
            with open('/tmp/update_downloaded.swu', "wb") as f:
                f.write(response.payload)
        
        return 0

    

if __name__ == "__main__":
    lwm2m = Lwm2m()

    while 1:
        pass
