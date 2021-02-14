import time

import pytest

from pysimpleapp.threads.simple_threads import SimpleThread
from pysimpleapp.message import Commands, Message, SubscriptionPackage


MIN_SLEEP = 1e-9


@pytest.fixture
def make_thread():

    created_threads = []

    def _make_thread(thread_class, *args, **kwargs):
        thread = thread_class(*args, **kwargs)
        created_threads.append(thread)
        return thread

    yield _make_thread

    for t in created_threads:
        while t.is_alive():
            t.end()
            min_sleep()


def min_sleep():
    time.sleep(MIN_SLEEP)


def send_subscription_message(
    thread: SimpleThread, queue, endpoint=SimpleThread.Endpoints.RESULT
):
    thread.message_queue.put(
        Message("Test", Commands.THREAD_SUBSCRIBE, SubscriptionPackage(endpoint, queue))
    )
