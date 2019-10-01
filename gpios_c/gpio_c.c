
#include <stdio.h> 
#include <stdlib.h>
#include <string.h> /* for memset */
#include <fcntl.h> 
#include <stdlib.h> 
#include <signal.h> 
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/ioctl.h>

#include "gpio_c.h"

int init_driver();

void (*python_callback)(int, int);

int fd;
struct sigaction sa;

typedef struct read_struct {
    unsigned int port;
    unsigned int value;
} read_struct;

typedef struct write_struct {
    unsigned int port;
    unsigned int value;
} write_struct;


int init_gpio_c(void (*callbackFunc)(int, int))
{
    python_callback = callbackFunc;

    init_driver();

    return 0;
}

int write_gpio_c(int port, int value) {
    write_struct wr;
    int ret;

    //The hardware has only 6 "out" Gpios
    if ((port < 0) && (port >= 6)) {
        printf(" [x] Invalid port number.\n");
        return -1;
    }

    wr.port = port;
    wr.value = value;

    ret = write(fd, &wr, sizeof(write_struct));

    return ret;
}

void driver_callback(int signo, siginfo_t *si, void *data) {
    read_struct rd;
    int ret;

    printf(" [*] Callback called in C.\n");

    ret = read(fd, &rd, sizeof(read_struct));

    if (ret < 0) {
        printf(" [x] Error reading the data.\n");
        return;
    }
    
    python_callback(rd.port, rd.value);
}

int init_driver() {    
    int oflags, retval = -99;

    // Open gpio file device for communication 
    fd = open("/dev/epsongpios", O_RDWR); 
    if (fd < 0) 
    { 
        fprintf(stderr, "\n [x] Gpio Driver Open Failed\n"); 
        exit(EXIT_FAILURE); 
    }

    sa.sa_sigaction = driver_callback;
    sa.sa_flags = SA_SIGINFO;
    sigemptyset(&sa.sa_mask);

    if (sigaction(SIGIO, &sa, NULL) == -1) {
        perror("sigaction");
        return -1;
    }

    // set this process as owner of device file
    retval = fcntl(fd, F_SETOWN, getpid());
    if(retval < 0) {
        printf(" [x] F_SETOWN fails \n");
    }

    // enable the gpio async notifications
    oflags = fcntl(fd, F_GETFL);
    retval = fcntl(fd, F_SETFL, oflags | FASYNC);

    if(retval < 0) {
        printf(" [x] F_SETFL Fails \n");
    }

    return retval;
}