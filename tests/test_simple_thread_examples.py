import threading
import time
from datetime import timedelta
from queue import Queue

import pytest
from tests.utils import min_sleep, send_subscription_message
from pysimpleapp.examples.threads import (
    ExampleSingleRunThread,
    ExampleMultiRunThread,
    ExampleAlternatingThread,
    ExampleRepeatingThread,
)
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


@pytest.mark.timeout(1, method="thread")
def test_alternating_endpoints_working_as_expected(make_thread):
    a = make_thread(ExampleAlternatingThread, "A")

    q_a = Queue()
    q_b = Queue()

    send_subscription_message(a, q_a, a.Endpoints.RESULT)
    send_subscription_message(a, q_b, a.Endpoints.NOT_RESULT)

    a.start()
    a.start()
    a.end()

    min_sleep()

    assert threading.active_count() == 2
    assert q_a.qsize() == 2
    assert q_b.qsize() == 2
    assert q_a.get().package is True
    assert q_a.get().package is False
    assert q_b.get().package is False
    assert q_b.get().package is True


@pytest.mark.timeout(1, method="thread")
def test_multi_run_thread_puts_message_in_all_queues(make_thread):
    m = make_thread(ExampleMultiRunThread, "M")

    q_a = Queue()
    q_b = Queue()

    send_subscription_message(m, q_a)
    send_subscription_message(m, q_b)
    m.start()
    m.start()
    m.start()
    m.start()
    m.end()

    min_sleep()

    assert threading.active_count() == 2
    assert q_a.qsize() == 4
    assert q_b.qsize() == 4
    q_a_results = [q_a.get().package for i in range(4)]
    q_b_results = [q_b.get().package for i in range(4)]
    assert q_a_results == [1, 2, 3, 4]
    assert q_b_results == [1, 2, 3, 4]


@pytest.mark.timeout(1, method="thread")
def test_example_repeating_test_runs_a_known_number_of_times(make_thread):
    r = make_thread(ExampleRepeatingThread, "R")

    q = Queue()

    # Set loop timer to be faster than usual
    r.loop_timer = timedelta(milliseconds=200)

    send_subscription_message(r, q)

    r.start()
    time.sleep(0.7)

    r.end()
    time.sleep(0.2)

    assert threading.active_count() == 2
    assert q.qsize() == 4
    q_results = [q.get().package for i in range(4)]
    assert q_results == [1, 2, 3, 4]
