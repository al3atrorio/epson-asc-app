
#ifndef __INIT_LWM2M_C_H__
#define __INIT_LWM2M_C_H__

int init_lwm2m_c(void (*callback)(int, const char *));
int set_string_c(char * node, char * data);
int set_integer_c(char * node, int data);
int set_integer_array_c(char * node, int data);

#endif //__INIT_LWM2M_C_H__



