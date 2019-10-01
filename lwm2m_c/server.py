from ctypes import *





def firmware_url_callback3():
    print("Callback recebida")
    



    

if __name__ == "__main__":

    CALLBACK2 = CFUNCTYPE(None)
    
    #lwm2m = Lwm2m2()

    #print("Chamando callcallback")

    #lwm2m.callcallback()

    #print("Entrando no loop")

    ptrs = []

    print("lwm2m sem class 4")
    _prime = CDLL('./teste.so')    
    callback = CALLBACK2(firmware_url_callback3)

    ini = api.init_lwm2m
    ini.argtypes = [callback]
    ini.restype = c_int

    ptrs.append(callback)

    print("chamando callback original")
    firmware_url_callback3()

    print("chamando callback")
    callback()

    print("registrando no c")

    _prime.init_lwm2m(callback)
    #print("ativando a callback")
    #_prime.callcallback()
    print("callback ativada")


    ptrs.append(callback)


    while 1:
        pass

    callback()
    firmware_url_callback3()
    _prime.init_lwm2m(callback)
        
