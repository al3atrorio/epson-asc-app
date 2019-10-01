from time import sleep

callback_python = None

cdef extern from "lwm2m_c.h":
    ctypedef void (*callback)(int, const char *)
    cdef int init_lwm2m_c(callback)
    cdef int set_string_c(char *, char *)
    cdef int set_integer_c(char *, int)
    cdef int set_integer_array_c(char *, int)

cdef void callback_c(int command, const char * value) with gil:
    print("Callback Recebida no Cython")
    str_command = str(command)
    str_value = value
    callback_python((command, str_value))

def init_lwm2m_client(callback):
    global callback_python
    callback_python = callback
    return init_lwm2m_c(callback_c)

def set_string_lwm2m(node, data):
    sleep(0.5)
    set_string_c(bytes(node, 'utf-8'), bytes(data, 'utf-8'))

def set_integer_lwm2m(node, data):
    sleep(0.5)
    set_integer_c(bytes(node, 'utf-8'), int(data))

def set_integer_array_lwm2m(node, data):
    sleep(0.5)
    set_integer_array_c(bytes(node, 'utf-8'), int(data))
