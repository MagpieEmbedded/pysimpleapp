import pytest

from tests.utils import min_sleep


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
