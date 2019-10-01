callback_python = None

cdef extern from "gpio_c.h":
    ctypedef void (*callback)(int, int)
    cdef void init_gpio_c(callback)
    cdef int write_gpio_c(int, int)

cdef void callback_c(int port, int value) with gil:
    print(" [*] Callback Recebida no Cython")
    callback_python(int(port), int(value))

def init_gpio_client(callback):
    global callback_python
    callback_python = callback
    init_gpio_c(callback_c)

def write_gpio(port, value):
    write_gpio_c(port, value)

