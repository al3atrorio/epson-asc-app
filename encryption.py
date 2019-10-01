from Crypto.Cipher import AES
from Crypto import Random

class Encryption:
    def __init__(self, key):
        self.encoder = PKCS7Encoder()
        self.key = bytes.fromhex(key)

    def encrypt(self, message):
        # 16 byte initialization vector
        iv = Random.new().read(AES.block_size)

        aes = AES.new(self.key, AES.MODE_CBC, iv[:16])

        # pad the plain text according to PKCS7
        pad_text = self.encoder.encode(bytes(message, 'utf-8'))

        # encrypt the padding text
        cipher = aes.encrypt(pad_text)

        return iv + cipher

    def decrypt(self, enc_message):
        aes = AES.new(self.key, AES.MODE_CBC, enc_message[:16])

        decipher = aes.decrypt(enc_message[16:])
        decrypted_message = self.encoder.decode(decipher)

        return decrypted_message.decode('utf-8')


class PKCS7Encoder:
    def decode(self, bytestring, k=16):
        """
        Remove the PKCS#7 padding from a text bytestring.
        """
        val = bytestring[-1]
        if val > k:
            raise ValueError('Input is not padded or padding is corrupt')
        l = len(bytestring) - val
        return bytestring[:l]


    ## @param bytestring    The text to encode.
    ## @param k             The padding block size.
    # @return bytestring    The padded bytestring.
    def encode(self, bytestring, k=16):
        """
        Pad an input bytestring according to PKCS#7        
        """
        l = len(bytestring)
        val = k - (l % k)
        return bytestring + bytearray([val] * val)

