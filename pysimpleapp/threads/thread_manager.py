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

ThreadManagers are always addressed with a list, whether the message is for the
thread manager or for a thread being managed.
The ThreadManager checks the first value in the address to ensure it should be processing
the message.
If it finds its own name, it replaces the receiver attribute of the message with a new tuple with
the first value sliced out.
If it does not find its own name, the message will be sent away to the output queue with
the name of the ThreadManager prepended to the front of the "from" message element.
This will allow complex patterns to be easily built up, with layers of ThreadManagers,
because threads do not need to know the whole hierarchy, only the name of their direct manager.
They can also contact sibling threads through the same mechanism as an external message
source, simplifying the ThreadManager code.

The top level ThreadManager (at the top of the hierarchy) will have None as its parent
as it was not created by a ThreadManager. Therefore, when it sends a message outside the
thread hierarchy, it will not prepend anything to the "from" address and therefore
the message address will be a valid place to send a reply.

This constructing and destructing of messages as they travel up and down ensures that
when a message is received by a thread, it can send a message back to the same location
and be sure that it is a valid location (or was when the message was sent).

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
A new thread with the same name cannot be created until the thread is neither an active thread
nor in the list of destroyed threads.
This will require some garbage collection of the ThreadManager.
Also a good function to return useful information about which names are currently being used

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
from queue import Queue

from pysimpleapp.threads.simple_threads import MultiRunThread
from pysimpleapp.message import Message


class ThreadManager(MultiRunThread):
    def __init__(self, name: str, owner: str, input_queue: Queue, output_queue: Queue):
        super().__init__(name, owner, input_queue, output_queue)
        # Dictionary of ThreadNames: ThreadTypes
        self.thread_types = {}

        # dict of active threads
        self.active_threads = {}
        # list of names of threads which have been destroyed and should have their output ignored
        self.destroyed_threads = []

        # Add functions
        self.address_book["NEW_THREAD"] = self.create_new_thread
        self.address_book["SET_THREAD_TYPES"] = self.set_thread_types

    def _message_handle(self, message: Message):
        """Takes a slightly different approach to messages as it needs to handle
        different situations"""

        self.logger.debug(
            f"MESSAGE Sender: {message.sender}, Command {message.command}, Package: {message.package}"
        )

        # Addressed to self
        if message.receiver == [self.name]:
            # Process as normal
            super()._message_handle(message)
        # Addressed to child thread
        elif self.name in message.receiver:
            # Strip name off front and pass on
            message.receiver = message.receiver[1:]
            # Send to appropriate thread input queue
            if message.receiver[0] in self.active_threads.keys():
                self.active_threads[message.receiver[0]].input_queue.put(message)
        else:
            # Check sender is not in list of destroyed threads
            if len(message.sender) > 1:
                if message.sender[1] not in self.destroyed_threads:
                    # Append name to front of sender and pass up
                    message.sender = [self.owner, *message.sender]
                    self.output_queue.put(message)
                else:
                    self.logger.error("Sender is a destroyed thread")
            else:
                self.logger.error("Sender does not have enough information")

    def create_new_thread(self, message: Message):
        """Create a new thread of the type requested"""
        # Extract message payload
        try:
            new_thread_name = message.package["thread_name"]
            new_thread_type = message.package["thread_type"]
        except KeyError:
            self.logger.error("Message did not contain thread name and thread type")
            # Exit function
            return

        # Check thread type exists
        if new_thread_type not in self.thread_types.keys():
            self.logger.error(
                f"Could not find thread type {new_thread_type} in thread types"
            )
            # Exit function
            return
        # Check thread name not already in use
        elif new_thread_name in self.active_threads.keys():
            self.logger.error(f"Thread name {new_thread_name} is currently in use")
            # Exit function
            return

        # Create the new thread and add it to the active_threads dictionary
        # Has it's own input queue and output queue points to thread manager input queue where it will be handled
        self.active_threads[new_thread_name] = self.thread_types[new_thread_type](
            new_thread_name, self.name, Queue(), self.input_queue
        )

    def set_thread_types(self, message: Message):
        """Update the thread types with the incoming message"""
        if type(message.package) == dict:
            self.thread_types.update(message.package)
        else:
            self.logger.error(
                "Could not find dictionary in message to update thread types"
            )

    def create_params(self):
        pass

    def main(self):
        pass
