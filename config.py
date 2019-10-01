import json
import os

class Config:
    def __init__(self):
        self.status = 'valid'

        with open("/tmp/application.json", "r") as config_file:
            self.config = json.load(config_file)

        self.rabbitmq = self.config["rabbitmq"]
        self.lwm2m = self.config["lwm2m"]
        self.mac = self.config["mac"]
        self.amqp_encryption_key = self.config["amqp_encryption_key"]
        self.wifi_enabled = self.config["wifi_enable"]
        self.rfids = self.config["rfids"]
        self.version = self.config["version"]
        self.web_enabled = os.path.isfile('/tmp/web_enabled')

        if self.validate_encryption_key(self.amqp_encryption_key) == False:
            print(" [x] Invalid Amqp Encryption Key")
            self.status = 'invalid'

        print(f" [*] Using Mac: {self.mac}")
        print( " [*] App config finished.")

    def validate_encryption_key(self, key):
        '''Key must have size 16, 24 or 32. Return True on success and False on error.'''

        try:
            bin_key = bytes.fromhex(key)

            if (len(bin_key) == 16) or (len(bin_key) == 24) or (len(bin_key) == 32):
                return True
        except Exception as e:
            print(e)

        return False
