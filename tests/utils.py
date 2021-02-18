import time

from pysimpleapp.threads.simple_threads import SimpleThread
from pysimpleapp.message import Commands, Message, SubscriptionPackage


MIN_SLEEP = 1e-2


def min_sleep():
    time.sleep(MIN_SLEEP)


def send_subscription_message(
    thread: SimpleThread, queue, endpoint=SimpleThread.Endpoints.RESULT
):
    thread.message_queue.put(
        Message("Test", Commands.THREAD_SUBSCRIBE, SubscriptionPackage(endpoint, queue))
    )
