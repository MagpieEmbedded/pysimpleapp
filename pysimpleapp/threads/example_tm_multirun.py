import threading
import time
from queue import Queue

from pysimpleapp.threads.examples import ExampleMultiRunThread
from pysimpleapp.threads.thread_manager import ThreadManager
from pysimpleapp.message import Message

if __name__ == "__main__":
    in_queue = Queue()
    out_queue = Queue()

    # See that all the threads are running
    print(f"Active threads: {threading.active_count()}")

    # Create the ThreadManager
    example_manager = ThreadManager("Example Manager", "Owner", in_queue, out_queue)
    # Set the thread types with human readable names
    in_queue.put(
        Message(
            "Owner",
            ["Example Manager"],
            "SET_THREAD_TYPES",
            {"Multi Run": ExampleMultiRunThread},
        )
    )

    # Create multipe Multi Run thread instances
    in_queue.put(
        Message(
            "Owner",
            ["Example Manager"],
            "NEW_THREAD",
            {"thread_name": "Multi 1", "thread_type": "Multi Run"},
        )
    )
    in_queue.put(
        Message(
            "Owner",
            ["Example Manager"],
            "NEW_THREAD",
            {"thread_name": "Multi 2", "thread_type": "Multi Run"},
        )
    )
    in_queue.put(
        Message(
            "Owner",
            ["Example Manager"],
            "NEW_THREAD",
            {"thread_name": "Multi 3", "thread_type": "Multi Run"},
        )
    )
    in_queue.put(
        Message(
            "Owner",
            ["Example Manager"],
            "NEW_THREAD",
            {"thread_name": "Multi 4", "thread_type": "Multi Run"},
        )
    )
    time.sleep(0.1)

    # See that all the threads are running
    print(
        f"Active threads: {threading.active_count()} - ThreadManger plus example threads"
    )

    # Take a look at the active threads
    print("Get information about the active threads from the Example Manager")
    in_queue.put(Message("Owner", ["Example Manager"], "ACTIVE_THREADS", None))
    msg = out_queue.get()
    print(msg)

    # Run the threads
    in_queue.put(Message("Owner", ["Example Manager", "Multi 1"], "THREAD_START", None))
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager", "Multi 2"], "THREAD_START", None))
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager", "Multi 3"], "THREAD_START", None))
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager", "Multi 4"], "THREAD_START", None))
    time.sleep(0.1)

    # Destroy one of the threads
    print("Destroy Multi 4")
    in_queue.put(
        Message(
            "Owner", ["Example Manager"], "DESTROY_THREAD", {"thread_name": "Multi 4"}
        )
    )
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager"], "ACTIVE_THREADS", None))
    msg = out_queue.get()
    print(msg)

    #  And run again
    in_queue.put(Message("Owner", ["Example Manager", "Multi 3"], "THREAD_START", None))
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager", "Multi 2"], "THREAD_START", None))
    time.sleep(0.1)
    in_queue.put(Message("Owner", ["Example Manager", "Multi 1"], "THREAD_START", None))
    time.sleep(0.1)

    # End the thread manager
    in_queue.put(Message("Owner", ["Example Manager"], "THREAD_END", None))
    time.sleep(0.1)

    # See that all the threads have stopped
    print(f"Active threads: {threading.active_count()}")
