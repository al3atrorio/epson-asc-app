#ifndef __INIT_GPIO_C_H__
#define __INIT_GPIO_C_H__

int init_gpio_c(void (*callback)(int, int));
int write_gpio_c(int, int);

#endif //__INIT_GPIO_C_H__