import threading
import time

import pytest
from pysimpleapp.examples.threads import ExampleSingleRunThread, ExampleMultiRunThread

MIN_SLEEP = 1e-9


def min_sleep():
    time.sleep(MIN_SLEEP)


@pytest.mark.timeout(1, method="thread")
def test_single_run_thread_finishes_straight_away():
    assert threading.active_count() == 2

    e = ExampleSingleRunThread("E")
    e.start()

    min_sleep()

    assert threading.active_count() == 2
