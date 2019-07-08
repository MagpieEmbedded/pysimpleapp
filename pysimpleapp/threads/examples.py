"""Some example implementations and runs of the simple_threads"""

import threading
from queue import Queue
import time

from pysimpleapp.threads.simple_threads import (
    SingleRunThread,
    MultiRunThread,
    RepeatingThread,
)
from pysimpleapp.message import Message


class ExampleSingleRunThread(SingleRunThread):
    def create_params(self):
        pass

    def main(self):
        print("Running single run thread...")


class ExampleMultiRunThread(MultiRunThread):
    def create_params(self):
        pass

    def main(self):
        print("Running multi run thread...")


class ExampleRepeatingThread(RepeatingThread):
    def create_params(self):
        pass

    def main(self):
        print("Running repeating thread...")


if __name__ == "__main__":
    in_queue = Queue()
    out_queue = Queue()

    owner = "Example Owner"

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
    time.sleep(1)

    print("Sending start messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_START", None))
    time.sleep(5)

    print("Sending stop messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_STOP", None))
    time.sleep(5)

    print("Sending start messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_START", None))
    time.sleep(5)

    print("Sending end messsage")
    in_queue.put(Message(owner, repeating_runner_name, "THREAD_END", None))
    time.sleep(5)

    print(f"Active Threads: {threading.active_count()}")

    print("All done!")
