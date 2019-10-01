from ctypes import *

def func():
    print("func called")
    
CALLBACK = CFUNCTYPE(None)
    
callback = CALLBACK(func)

print("Calling callback 4")
callback()

print("Done!")

        
