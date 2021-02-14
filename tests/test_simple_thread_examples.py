import threading
import time
from queue import Queue

import pytest
from tests.utils import make_thread, min_sleep, send_subscription_message
from pysimpleapp.examples.threads import ExampleSingleRunThread, ExampleMultiRunThread
from pysimpleapp.message import Message, Commands


@pytest.mark.timeout(1, method="thread")
def test_single_run_thread_finishes_straight_away():
    assert threading.active_count() == 2

    e = ExampleSingleRunThread("E")
    e.start()

    assert threading.active_count() == 3

    min_sleep()

    assert threading.active_count() == 2


@pytest.mark.timeout(1, method="thread")
def test_single_run_thread_ends_straight_away():
    assert threading.active_count() == 2

    e = ExampleSingleRunThread("E")
    assert threading.active_count() == 3

    e.end()
    min_sleep()

    assert threading.active_count() == 2


@pytest.mark.timeout(1, method="thread")
def test_multi_run_thread_runs_then_ends():
    assert threading.active_count() == 2

    m = ExampleMultiRunThread("M")
    assert threading.active_count() == 3

    m.start()
    m.start()
    m.start()
    m.start()
    min_sleep()

    assert m.times_ran == 4

    m.end()
    min_sleep()

    assert threading.active_count() == 2


@pytest.mark.timeout(1, method="thread")
def test_single_run_thread_puts_message_in_queue(make_thread):
    e = make_thread(ExampleSingleRunThread, "E")

    q = Queue()

    send_subscription_message(e, q)
    e.start()

    min_sleep()

    assert threading.active_count() == 2
    assert q.qsize() == 1
    assert q.get() == Message("E", Commands.THREAD_HANDLE, None)


@pytest.mark.timeout(1, method="thread")
def test_multi_run_thread_puts_message_in_queue(make_thread):
    m = make_thread(ExampleMultiRunThread, "M")

    q = Queue()

    send_subscription_message(m, q)
    m.start()
    m.start()
    m.start()
    m.start()
    m.end()

    min_sleep()

    assert threading.active_count() == 2
    assert q.qsize() == 4
    assert q.get() == Message("M", Commands.THREAD_HANDLE, 1)
    assert q.get() == Message("M", Commands.THREAD_HANDLE, 2)
    assert q.get() == Message("M", Commands.THREAD_HANDLE, 3)
    assert q.get() == Message("M", Commands.THREAD_HANDLE, 4)
