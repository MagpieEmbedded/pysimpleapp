"""Some example implementations and runs of the simple_threads"""

import threading
from queue import Queue
import logging
import time

from pysimpleapp.threads.simple_threads import (
    SingleRunThread,
    MultiRunThread,
    RepeatingThread,
    PreciseRepeatingThread,
)
from pysimpleapp.message import Message


class ExampleSingleRunThread(SingleRunThread):
    def create_params(self):
        pass

    def main(self):
        print("Running single run thread...")


class ExampleMultiRunThread(MultiRunThread):
    def create_params(self):
        self.times_ran = 1

    def main(self):
        print(f"Running multi run thread called {self.name} {self.times_ran} times")
        self.times_ran += 1


class ExampleRepeatingThread(RepeatingThread):
    def create_params(self):
        pass

    def _thread_start(self, message: Message):
        super()._thread_start(message)
        self.start_time = time.time()

    def main(self):
        print(
            f"Running thread {time.time() - self.start_time:.3f}s after start command"
        )
        time.sleep(0.2)


class ExamplePreciseThread(PreciseRepeatingThread):
    def create_params(self):
        pass

    def _thread_start(self, message: Message):
        super()._thread_start(message)
        self.start_time = time.time()

    def main(self):
        print(
            f"Precise thread {time.time() - self.start_time:.3f}s after start command"
        )
        time.sleep(0.2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    in_queue = Queue()
    out_queue = Queue()

    owner = "Example Owner"

    active_threads = threading.active_count()

    print(f"Threads at start: {threading.active_count()}")

    print("Creating single run thread")
    single_runner_name = "Example Single Run Thread"
    single_runner = ExampleSingleRunThread(
        single_runner_name, owner, in_queue, out_queue
    )
    print(f"Active Threads: {threading.active_count()}")
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, single_runner_name, "THREAD_START", None))
    time.sleep(1)

    print(f"Active Threads: {threading.active_count()}")
    time.sleep(1)

    print("Creating multi run thread")
    multi_runner_name = "Example Multi Run Thread"
    multi_runner = ExampleMultiRunThread(multi_runner_name, owner, in_queue, out_queue)
    print(f"Active Threads: {threading.active_count()}")
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, multi_runner_name, "THREAD_START", None))
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, multi_runner_name, "THREAD_START", None))
    print("Sending start messsage")
    in_queue.put(Message(owner, multi_runner_name, "THREAD_START", None))
    time.sleep(1)

    print("Sending end messsage")
    in_queue.put(Message(owner, multi_runner_name, "THREAD_END", None))
    time.sleep(1)

    print(f"Active Threads: {threading.active_count()}")
    time.sleep(1)

    print(f"Creating repeating thread")
    repeating_runner_name = "Example Repeating Thread"
    repeating_runner = ExampleRepeatingThread(
        repeating_runner_name, owner, in_queue, out_queue
    )
    print(f"Active Threads: {threading.active_count()}")
    in_queue.put(
        Message(owner, repeating_runner_name, "THREAD_UPDATE", {"loop_timer": 5})
    )
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_START", None))
    time.sleep(7)

    in_queue.put(Message(owner, repeating_runner_name, "THREAD_STOP", None))
    in_queue.put(
        Message(owner, repeating_runner_name, "THREAD_UPDATE", {"loop_timer": 0.5})
    )
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_START", None))
    time.sleep(5)

    print("Sending end messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_END", None))
    time.sleep(1)

    print(f"Active Threads: {threading.active_count()}")

    print("All done!")

    print(f"Active Threads: {threading.active_count()}")
    time.sleep(1)

    print(f"Creating precise thread")
    precise_runner_name = "Example Precise Thread"
    precise_runner = ExamplePreciseThread(
        precise_runner_name, owner, in_queue, out_queue
    )
    print(f"Active Threads: {threading.active_count()}")
    print(f"{precise_runner.parameters}")
    in_queue.put(
        Message(owner, precise_runner_name, "THREAD_UPDATE", {"loop_timer": 5})
    )
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, precise_runner_name, "THREAD_START", None))
    time.sleep(7)

    in_queue.put(Message(owner, precise_runner_name, "THREAD_STOP", None))
    in_queue.put(
        Message(owner, precise_runner_name, "SET_LOOP_TIMER", {"loop_timer": 0.5})
    )
    in_queue.put(Message(owner, precise_runner_name, "THREAD_START", None))
    time.sleep(5)

    in_queue.put(
        Message(owner, precise_runner_name, "SET_LOOP_TIMER", {"loop_timer": 0.1})
    )
    time.sleep(5)

    in_queue.put(
        Message(owner, precise_runner_name, "SET_LOOP_TIMER", {"loop_timer": 1.0})
    )
    time.sleep(10)

    print("Sending end messsage")
    in_queue.put(Message(owner, precise_runner_name, "THREAD_END", None))
    time.sleep(1)

    print(f"Active Threads: {threading.active_count()}")

    print("All done!")

    assert (
        threading.active_count() == active_threads
    ), f"Started with {active_threads} threads, finished with {threading.active_count()} :("
