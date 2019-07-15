"""ThreadManager is a special thread which is designed make it easier to control
many threads at the same time.

It is a subclass of the MultiRunThread and manages the flow of information to and
from running thread instances.
It is addressed with the same commands as the MultiRunThread, with the special commands
SET_THREAD_TYPES, NEW_THREAD and DESTROY_THREAD, all of which are explained below.

The ThreadManager has a special dictionary of thread_types which may be set with the
command SET_THREAD_TYPES.
This maps human readable strings or identifiers to the more complex class names
of thread types.
It also means the operating the ThreadManager does not require importing the thread
classes themselves locally, as this will have been done when the ThreadManager was
setup, all that needs to be known is the identifier.

ThreadManagers are always addressed with a tuple or list, whether the message is for the 
thread manager or for a thread being managed.
The ThreadManager checks the first value in the address to ensure it should be processing
the message.
If it finds its own name, it replaces the receiver attribute of the message with a new tuple with
the first value sliced out.
If it does not find its own name, the message will be sent away to the output queue.
This will allow complex patterns to be easily built up, with layers of ThreadManagers,
because threads do not need to know that they are being managed or at what level of
the heirarchy they are, and neither does the TheadManager.

To create a new thread with the thread manager, send a NEW_THREAD command directly to the
thread manager and provide a dictionary containing values for the *thread type*. 
The ThreadManager will look in its list of currently active threads
to see if it has a thread with that name. If it does, the request will be rejected.
If not, a new thread of that type and with that name will be created, with the
owner being the name of the ThreadManager.

From then on, the thread will be addressed through the ThreadManager with an address
of [*thread_manager_name*, *thread_name*]. 

Each thread being manager by a ThreadManager has its own internal input queue to receive
messsages. This prevents name clashing which would inevitably occur by using a single queue
for many threads.

Output queues from the threads are connected to the ThreadManager input queue, to be
processed the same way as messages external to the ThreadManager.
This allows the ThreadManager to wait for input on **one** queue only and to process
all messages the same way.
It also opens up the potential for threads to contact other threads, although this situation
should be managed carefully.

Threads which are running happily are kept in the ThreadManager's active thread list.
The ThreadManager will preiodically review this list to see if any of the threads are stopped.
Threads which are stopped are removed from the list.

Occasionally, it may be necessary to ask the ThreadManager to kill a thread and prevent
its output from being sent.
This might be the case if a thread has *main* function which takes a long time and sends
a big message at the end, but is no longer needed.
In this case, send a DESTROY_THREAD command directly to the ThreadManager with the name
of the thread to be destroyed as the package.
In this case, the thread will be moved to a list of threads to be destroyed and the output
will be captured by the ThreadManager instead of being sent onwards.

**Example:**

.. code-block:: python

    from pysimpleapp.threads.examples import ExampleMultiRunThread
    from pysimpleapp.threads import ThreadManager
    from pysimpleapp.message import Message
    from queue import Queue

    in_queue = Queue()
    out_queue = Queue()

    # Create the ThreadManager
    example_manager = ThreadManager("Example Manager", "Owner", in_queue, out_queue)
    # Set the thread types with human readable names
    in_queue.put(Message("Owner", "Example Manager", "SET_THREAD_TYPES", {"Multi Run": ExampleMultiRunThread}))

    # Create multipe Multi Run thread instances
    in_queue.put(Message("Owner", ["Example Manager"], "NEW_THREAD", {"thread_name": "Multi 1", "thread_type": "Multi Run"}))
    in_queue.put(Message("Owner", ["Example Manager"], "NEW_THREAD", {"thread_name": "Multi 2", "thread_type": "Multi Run"}))
    in_queue.put(Message("Owner", ["Example Manager"], "NEW_THREAD", {"thread_name": "Multi 3", "thread_type": "Multi Run"}))

    # See that all the threads are running
    import threading
    threading.active_count()

    # Run the threads
    in_queue.put(Message("Owner", ["Example Manager", "Multi 1"], "THREAD_START", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 2"], "THREAD_START", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 3"], "THREAD_START", None))

    #  And again
    in_queue.put(Message("Owner", ["Example Manager", "Multi 3"], "THREAD_START", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 2"], "THREAD_START", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 1"], "THREAD_START", None))

    # End the threads
    in_queue.put(Message("Owner", ["Example Manager", "Multi 1"], "THREAD_END", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 2"], "THREAD_END", None))
    in_queue.put(Message("Owner", ["Example Manager", "Multi 3"], "THREAD_END", None))

"""
