#include <stdlib.h>
#include <stdio.h>
#include <string.h> /* for memset */
#include <unistd.h>
#include <pthread.h>

#include <awa/common.h>
#include <awa/client.h>

#include "lwm2m_c.h"

#define IPC_PORT (12345)
#define IPC_ADDRESS "127.0.0.1"
#define OPERATION_PERFORM_TIMEOUT 1000

void *lwm2m_thread_function();

int subscribe(AwaClientChangeSubscription ** subscription, 
                char * node, 
                void (*callback)(const AwaChangeSet * changeSet, void * context), 
                char * data);
int subscribe_execute(AwaClientExecuteSubscription ** subscription, 
                char * node, 
                void (*callback)(const AwaExecuteArguments * arguments, void * context), 
                char * data);
int cancelSubscription(AwaClientChangeSubscription ** subscription);

pthread_t           lwm2m_thread;
pthread_mutex_t     lwm2m_mutex;

AwaClientSession * session;
AwaClientChangeSubscription * subscription_url;
AwaClientExecuteSubscription * subscription_execute;

void (*python_callback)(int, const char *);

/*
 * This function will be called by the API when the client sends
 * a notification of change. When invoked, changeSet provides information
 * about the value(s) that triggered the notification, and context
 * is the supplied pointer to any application data.
 */
static void urlCallback(const AwaChangeSet * changeSet, void * context)
{
    const char * userData = (const char *)context;
    printf(" [*] Callback received. Context = %s\n", userData);

    const char * value;

    AwaChangeSet_GetValueAsCStringPointer(changeSet, "/5/0/1", &value);
    printf(" [*] Value of resource /5/0/1 changed to: %s\n", value);
    printf(" [*] Callback Address: %p\n", python_callback);

    python_callback(1, value);
    printf(" [*] Callback called\n");
}

static void executeCallback(const AwaExecuteArguments * arguments, void * context)
{
    printf(" [*] Execute Callback triggered\n");
    python_callback(2, "execute");
}

int init_lwm2m_c(void (*callbackFunc)(int, const char *))
{
    AwaError result;
    python_callback = callbackFunc;

    /* Create and initialise client session */
    session = AwaClientSession_New();

    /* Use default IPC configuration */
    result = AwaClientSession_Connect(session);

    if (result != AwaError_Success) {
        return 2;
    }

    subscribe(&subscription_url, "/5/0/1", urlCallback, "Firmware Update - URL");
    subscribe_execute(&subscription_execute, "/5/0/2", executeCallback, "Firmware Update - Execute");

    if(!pthread_create(&lwm2m_thread, NULL, lwm2m_thread_function, NULL)) {
		printf(" [*] Lwm2m Thread Created.\n");
	}
	else {
		printf(" [x] ERROR - Could not create the Dispatcher Thread.\n");
		return 1;
	}

    return 0;
}

int subscribe(AwaClientChangeSubscription ** subscription, 
                char * node, 
                void (*callback)(const AwaChangeSet * changeSet, void * context), 
                char * data) {
    /*
     * Create a new change subscription to resource "node".
     * Data can be provided to the callback function via the "data" pointer.
     */
    *subscription = AwaClientChangeSubscription_New(node, callback, (void *)data);

    /* Start listening to notifications */
    AwaClientSubscribeOperation * subscribeOperation = AwaClientSubscribeOperation_New(session);
    AwaClientSubscribeOperation_AddChangeSubscription(subscribeOperation, *subscription);
    AwaClientSubscribeOperation_Perform(subscribeOperation, OPERATION_PERFORM_TIMEOUT);
    AwaClientSubscribeOperation_Free(&subscribeOperation );
}

int subscribe_execute(AwaClientExecuteSubscription ** subscription, 
                char * node, 
                void (*callback)(const AwaExecuteArguments * arguments, void * context), 
                char * data) {
    /*
     * Create a new change subscription to resource "node".
     * Data can be provided to the callback function via the "data" pointer.
     */
    *subscription = AwaClientExecuteSubscription_New(node, callback, (void *)data);

    /* Start listening to notifications */
    AwaClientSubscribeOperation * subscribeOperation = AwaClientSubscribeOperation_New(session);
    AwaClientSubscribeOperation_AddExecuteSubscription(subscribeOperation, *subscription);
    AwaClientSubscribeOperation_Perform(subscribeOperation, OPERATION_PERFORM_TIMEOUT);
    AwaClientSubscribeOperation_Free(&subscribeOperation );
}

int set_string_c(char * node, char * data) {
    /* Create SET operation */
    AwaClientSetOperation * set_operation = AwaClientSetOperation_New(session);

    /* Provide a path and value for the resource */
    AwaClientSetOperation_AddValueAsCString(set_operation, node, data);

    /* Perform the SET operation */
    AwaClientSetOperation_Perform(set_operation, OPERATION_PERFORM_TIMEOUT);

    /* Operations must be freed after use */
    AwaClientSetOperation_Free(&set_operation);
}

int set_integer_c(char * node, int data) {
    /* Create SET operation */
    AwaClientSetOperation * set_operation = AwaClientSetOperation_New(session);

    /* Provide a path and value for the resource */
    AwaClientSetOperation_AddValueAsInteger(set_operation, node, data);

    /* Perform the SET operation */
    AwaClientSetOperation_Perform(set_operation, OPERATION_PERFORM_TIMEOUT);

    /* Operations must be freed after use */
    AwaClientSetOperation_Free(&set_operation);
}

int set_integer_array_c(char * node, int data) {


    //This resource is a collection, we create the array
    AwaIntegerArray * data_array = AwaIntegerArray_New();
    
    //Adding the value to position 0 of the array
    AwaIntegerArray_SetValue(data_array, 0, data);

    /* Create SET operation */
    AwaClientSetOperation * set_operation = AwaClientSetOperation_New(session);

    /* Provide a path and value for the resource */
    AwaClientSetOperation_AddValueAsIntegerArray(set_operation, node, data_array);

    /* Perform the SET operation */
    AwaClientSetOperation_Perform(set_operation, OPERATION_PERFORM_TIMEOUT);

    /* Operations must be freed after use */
    AwaClientSetOperation_Free(&set_operation);
}

void *lwm2m_thread_function() {
    printf(" [*] Lwm2m Thread Running...\n");
    while (1) {
        /* Receive notifications */
        if (AwaClientSession_Process(session, OPERATION_PERFORM_TIMEOUT) == AwaError_Success) {
            AwaClientSession_DispatchCallbacks(session);
        }
    }
}

int deinit_lwm2m(void)
{
    cancelSubscription(&subscription_url);

    AwaClientSession_Disconnect(session);
    AwaClientSession_Free(&session);

    return 0;
}

int cancelSubscription(AwaClientChangeSubscription ** subscription) {
    /* Unsubscribe  */
    AwaClientSubscribeOperation * cancelSubscribeOperation = AwaClientSubscribeOperation_New(session);
    AwaClientSubscribeOperation_AddCancelChangeSubscription(cancelSubscribeOperation, *subscription);
    AwaClientSubscribeOperation_Perform(cancelSubscribeOperation, OPERATION_PERFORM_TIMEOUT);
    AwaClientSubscribeOperation_Free(&cancelSubscribeOperation);

    /* Free the change subscription */
    AwaClientChangeSubscription_Free(subscription);

    return 0;
}
