

all:

	$(HOST_DIR)/bin/cython -3 lwm2m_c/lwm2m_client.pyx
	$(CC) -g -O2 -fpic -c lwm2m_c/lwm2m_client.c -o lwm2m_client.o -I$(STAGING_DIR)/usr/include/python3.6m/
	$(CC) -g -O2 -fpic -c lwm2m_c/lwm2m_c.c -o lwm2m_c.o
	$(CC) -g -O2 -shared -o lwm2m_client.so lwm2m_c.o lwm2m_client.o -lpython3.6m -lawa -lpthread -ldl  -lutil -lm

	$(HOST_DIR)/bin/cython -3 gpios_c/gpio_client.pyx
	$(CC) -g -O2 -fpic -c gpios_c/gpio_client.c -o gpio_client.o -I$(STAGING_DIR)/usr/include/python3.6m/
	$(CC) -g -O2 -fpic -c gpios_c/gpio_c.c -o gpio_c.o
	$(CC) -g -O2 -shared -o gpio_client.so gpio_c.o gpio_client.o -lpython3.6m -ldl  -lutil -lm

	rm *.o
