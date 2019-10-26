import time
import threading
from queue import Queue

from pysimpleapp.message import Message
from pysimpleapp.thread_manager import ThreadManager
from pysimpleapp.examples.thread_examples import ExampleSingleRunThread

if __name__ == "__main__":

    in_queue = Queue()
    out_queue = Queue()

    manager = "Example Manager"
    owner = "Owner"

    print(f"Active Threads: {threading.active_count()}")

    # Create the ThreadManager
    print("Creating Example Manager")
    example_manager = ThreadManager(manager, owner, in_queue, out_queue)
    print(f"Active Threads: {threading.active_count()}")

    # Supply a dictionary of thread types
    print("Providing thread types")
    in_queue.put(
        Message(
            owner, [manager], "SET_THREAD_TYPES", {"Single Run": ExampleSingleRunThread}
        )
    )

    # Create a new single run thread
    print("New single run thread")
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": "S1", "thread_type": "Single Run"},
        )
    )
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")

    # Run the thread
    print("Send command to run single run thread")
    in_queue.put(Message(owner, [manager, "S1"], "THREAD_START", None))
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")

    # Create a new single run thread
    print("New single run thread")
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": "S2", "thread_type": "Single Run"},
        )
    )
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")
    # Create a new single run thread
    print("New single run thread")
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": "S3", "thread_type": "Single Run"},
        )
    )
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")
    # Create a new single run thread
    print("New single run thread")
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": "S4", "thread_type": "Single Run"},
        )
    )
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")

    print("Ending Example Manager and child threads")
    in_queue.put(Message(owner, [manager], "THREAD_END", None))
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")
