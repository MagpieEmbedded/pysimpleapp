import threading
import time

import pytest
from tests.utils import min_sleep
from pysimpleapp.examples.threads import ExampleSingleRunThread, ExampleMultiRunThread


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
