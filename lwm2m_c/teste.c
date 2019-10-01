#include <stdlib.h>
#include <stdio.h>
#include <string.h> /* for memset */
#include <unistd.h>

//void *lwm2m();
int init_lwm2m(void * (*callbackFunc)(void));
//int teste//

//void * (*python_callback)();

typedef void *cb(void);

int init_lwm2m(cb callbackFunc)
{
    printf("Doug5\n");
    char commands[] = "TEstando Doug";
    //python_callback = callbackFunc;

    callbackFunc();

    return 0;
}

//int teste() {
 //   printf("teste\n");

//    return 1;
//}

//void callcallback() {
//    printf("Doug chamando callback\n\n");
//    python_callback();
//}

