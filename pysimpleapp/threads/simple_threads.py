"""
Module with subclasses of threading module which have been
altered to fit within the pysimpleapp system.

Threads should have the ability to be started and stopped on command
They should also have parameters which can be set before the thread
is run.
"""

import threading
from enum import Enum, unique
from typing import List, Tuple, Set
from queue import Queue
import logging
from pysimpleapp.message import Commands, Message
import time
from datetime import timedelta
from abc import ABC, abstractmethod


# Define endpoints
@unique
class Endpoints(Enum):
    RESULT = "result"


class SimpleThread(ABC, threading.Thread):
    """
    ***SimpleThread*** is an abstract class which will provide the basis for building out the threads provided in **pysimpleapp**.

    Methods which must be specified by children:

    * *create_params* - creates the parameters which should be used during *main* execution
    * *main* - the body of the thread which performs the functionality
    * *_control_loop* - describes how the class executes the main function

    It executes its *main* function as part of a control loop which is specified by child classes.
    Before it starts, the parameters can be updated and it can even be ended and prevented from ever running.

    Must be initialised with a name, owner, input and output queues.

    The operation of the thread is implemented in *main()*
    This function should be overridden during implementation.

    Parameters are created in *create_params()* which should be overridden when implemented.
    Parameters should not be created from anywhere else.
    Updates to the parameter will be collected after each run of the *main* function.

    Messages are handled based on a lookup table called the *address_book*.
    There are some in-built commands which can be easily accessed, but the addresses can be changed easily.
    To add custom commands to the thread, simply create a function in the class which takes a
    *pysimpleapp.message.Message* object and give it a key in the address book.

    **Example**

    .. code-block:: python

        self.address_book["my_custom_command"] = self.my_custom_command_handler

        # During message handling, this will be called as:
        self.address_book["my_custom_command"](messsage)

    """

    Endpoints = Endpoints

    def __init__(self, name: str):
        """
        Create the thread, set up control flags and call _create_params

        :param name: Identifier for the thread, could be list of strings depending on communication model
        :param owner: Address of object which created the thread (often a ThreadManager)
        :param message_queue: Input pipe for messages which the thread is expected to process
        """
        # Create thread
        super().__init__(name=name)
        # Set attributes
        self.message_queue = Queue()

        # Give the logger name of the thread for debugging
        self.logger = logging.getLogger(f"{type(self).__name__}-{self.name}")

        # Create control flags - some of these are for use in more complex threads
        self.start_flag = threading.Event()
        self.stop_flag = threading.Event()
        self.end_flag = threading.Event()

        # Store the callbacks related to message commands
        self.command_callbacks = {
            Commands.THREAD_START: self._thread_start,
            Commands.THREAD_STOP: self._thread_stop,
            Commands.THREAD_END: self._thread_end,
            Commands.THREAD_SUBSCRIBE: self._thread_subscribe,
            Commands.THREAD_HANDLE: self.custom_handler,
        }

        # Dictionary for handling subscriptions
        self.subscriptions: dict[Set[Tuple(str)], Queue] = {
            endpoint: [] for endpoint in list(self.Endpoints)
        }

        # Create parameters
        self.parameters = {}
        self.setup()

        # Start thread object running
        threading.Thread.start(self)

    @abstractmethod
    def main(self):
        """
        Override this function to provide the thread with instructions.

        *main* provides the functionality for the thread.
        It may contain heavy computations, IO processing and anything you want to do without having to worry about
        *exactly* how long it takes.

        **Good ideas:**

        * Read from parameters to decide on program execution
        * Send *pysimpleapp.Message* to endpoints where they will be sent to subscribers
        * Handle exceptions to prevent unnecessary failures of the thread

        **Bad ideas:**

        * Writing to parameters *during* program execution
        * Writing things back to the *input_queue*
        * Implementing operations which take a long time to complete and expecting fast reactions in changes to parameters or THREAD_STOP commands
        """
        pass

    @abstractmethod
    def setup(self):
        """
        Override this function to do whatever setup is necessary for the thread.
        Example:

        .. code-block:: python

            self.parameters["param 1"] = 0
            self.parameters["param 2"] = "some string"

        """
        pass

    def _thread_start(self, message: Message):
        """Handle a start message by setting the start flag"""
        self.start_flag.set()

    def _thread_stop(self, message: Message):
        """Handle a stop message by setting the stop flag"""
        self.stop_flag.set()

    def _thread_end(self, message: Message):
        """Handle an end message by setting the end flag"""
        self.end_flag.set()

    def _thread_subscribe(self, message: Message):
        """
        Handle a subscription flag by putting the provided queue
        in the appropriate endpoint
        """
        try:
            self.subscriptions[message.package.endpoint].append(message.package.queue)
        except KeyError as e:
            self.logger.error(f"Could not find endpoint {message.package.endpoint}")
            raise e

    def custom_handler(self, message: Message):
        """
        Override this function to handle custom user messages.
        Expect a *pysimpleapp.Message* object as an input, no return value is expected or handled by default

        **Good idea:**
        Include a command as a key in a package dictionary to reliably handle custom messages.
        This will be much clearer than sorting by type, size or looking for a specific key or list value.
        """
        pass

    def _update_params(self, message: Message):
        """
        Update parameters with new values if the parameter is available.

        If the parameter is not found, this will be recorded in the log as an error but will not crash the thread.

        :param new_params: Dictionary with one or more parameters to update.
        Must already have been created in *_create_params"
        """
        new_params = message.package

        try:
            assert type(new_params) == dict
        except AssertionError:
            self.logger.error(
                f"Expected dictionary as package for parameter update, got {message}"
            )

        for key, value in new_params.items():
            if key in self.parameters.keys():
                self.parameters[key] = value
            else:
                self.logger.error(
                    f"Could not find {key} parameter in parameters for thread {self.name}"
                )

    def _message_handle(self, message: Message):
        """Handle incoming messages.

        Expects messages to *pysimpleapp.Message* objects
        :params message: A *pysimpleapp.Message* object to process
        """
        # Log the message
        self.logger.debug(
            f"MESSAGE Sender: {message.sender}, Command {message.command}, Package: {message.package}"
        )

        # Try to execute the command specified in the address book, otherwise raise an error
        try:
            self.command_callbacks[message.command](message)
        except KeyError as e:
            logging.error(
                f"Expected command in {self.address_book.keys()}, got {message.command} in message: {message}"
            )
            raise e
        except Exception:
            raise

        return

    @abstractmethod
    def _control_loop(self):
        """
        This defines the programatic flow for the thread.

        Executes the main function and defines how things are handled.
        """
        pass

    def run(self):
        """
        This defines the programatic flow for the thread.

        Threads wait for messages on the *input_queue* and then process them.

        If an end command is given, the thread will return **True** and exit, therefore no longer being able to run.

        If a start command is given and no end command is requested, the *_control_loop* function will be called.
        While running, the queue will not be processed.

        If the control loop raises an exception, the thread will exit gracefully.
        """
        while self.end_flag.is_set() is False:
            # Get message from input queue and handle it
            message = self.message_queue.get()
            self._message_handle(message)

            # Check whether start flag has been raised
            if self.start_flag.is_set():
                # Clear the flag to prevent running continuously
                self.start_flag.clear()

                # Run the control loop
                self._control_loop()

        # Return true and exit
        return True

    def start(self):
        """Put THREAD_START message in queue"""
        self.message_queue.put(Message((self.name,), Commands.THREAD_START, None))

    def stop(self):
        """Put THREAD_STOP message in queue"""
        self.message_queue.put(Message((self.name,), Commands.THREAD_STOP, None))

    def end(self):
        """Put THREAD_END message in queue"""
        self.message_queue.put(Message((self.name,), Commands.THREAD_END, None))

    def publish(
        self, package, endpoint=Endpoints.RESULT, command=Commands.THREAD_HANDLE
    ):
        """
        Publishes a package to all the subscribers of an endpoint

        By default, will publish to the RESULT endpoint with a command of THREAD_HANDLE.
        You may wish to provide a different endpoint or command depending on how
        the application is set up.
        """
        try:
            for queue in self.subscriptions[endpoint]:
                queue.put(Message(self.name, command, package))
        except KeyError:
            logging.error(
                f"Thread {self.name} trying to publish to endpoint {endpoint} which was not created"
            )
            raise
        except AttributeError:
            logging.error(
                f"Thread {self.name} trying to publish to endpoint {endpoint} which was not created"
            )
            raise
        except Exception:
            logging.error(
                f"Isse publishing to endpoing {endpoint} on thread {self.name}"
            )
            raise

    def send_to(self, receiver: List[str], command: str, package: any):
        """Helper function for sending information from a thread correctly"""
        self.output_queue.put(
            Message([self.owner, self.name], receiver, command, package)
        )


class MultiRunThread(SimpleThread):
    """
    ***MultiRunThread*** is a child of ***SimpleThread*** which may run the *main* function repeatedly.

    It will execute after a start command, and then await further instruction.
    This may be another start command, in which case the *main* function will repeat.
    Or it may be an update or end command, which will cause the parameters to update or the thread to end, respectively.

    Other than that, it works exactly the same way as the ***SimpleThread***.

    *main* and *_create_params* are left as abstract methods for the user to implement.
    """

    def _control_loop(self):
        """Execute the main function and then return to waiting for messages"""
        self.main()


class SingleRunThread(SimpleThread):
    """
    ***SingleRunThread*** is a child of ***SimpleThread*** which runs the *main* function once and then ends.

    It will execute after a start command and then exit.

    *main* and *create_params* are left as abstract methods for the user to implement.
    """

    def _control_loop(self):
        """Execute the main function and set the end flag immediately"""
        self.main()
        self.end_flag.set()


class RepeatingThread(SimpleThread):
    """
    ***RepeatingThread*** is a child of ***SimpleThread*** which runs its *main* function on a regular basis.

    It differs from ***MultiRunThread*** in that once it has been started, it will trigger its own runs.
    It may be stopped with the "THREAD_STOP" command.
    Having received such a command, the thread will be waiting to start again and will not end without
    a THREAD_END command.

    RepeatingThread has a parameter of "loop_timer" which specifies the time, in seconds,
    after program execution to wait before running *main* again.
    Default is 1s.

    This is achieved by adding a start message to its own input queue after "loop_timer" amount of time.
    Therefore, it is susceptible to being flooded by other messages.
    It may also be triggered by sending another start command.

    So, to use safely, set parameters before starting and do not flood with parameters while running.
    Issue a THREAD_STOP command before performing large changes to the parameters.

    *main* and *create_params* are left as abstract methods for the user to implement.
    """

    def __init__(self, name: str, interval: timedelta = timedelta(seconds=1)):
        super().__init__(name)
        # Add loop timer parameter to describe how often function should run
        self.loop_timer = timedelta
        # Add repeat function to address book
        self.command_callbacks["THREAD_REPEAT"] = self._thread_repeat
        # Hold onto the current timer to cancel if necessary
        self.repeat_timer = None

    def cancel_timer(self):
        if self.repeat_timer:
            self.repeat_timer.cancel()

    def _thread_repeat(self, message: Message):
        """
        Raises the start flag but does not clear stop flag.
        This prevents the repeating command from overriding a stop command.
        """
        self.start_flag.set()

    def _thread_start(self, message: Message):
        """
        Thread start in a repeating thread raises start flag and also clears stop flag.
        This ensures that a THREAD_START command will always trigger a main run.

        Cancel the repeat_timer if it is currently waiting to ensure timing starts from this point
        """
        self.start_flag.set()
        self.stop_flag.clear()
        self.cancel_timer()

    def _thread_stop(self, message: Message):
        """Raise the stop flag and cancel the current timer"""
        self.stop_flag.set()
        self.cancel_timer()

    def _thread_end(self, message):
        self.end_flag.set()
        self.cancel_timer()

    def repeating_start(self):
        """Command to set the *main* function going again"""
        self.message_queue.put(Message(self.name, "THREAD_REPEAT", None))

    def _control_loop(self):
        """Run the main function and set a timer on sending a new start command, unless the stop flag is raised."""
        if not self.stop_flag.is_set():
            self.main()
            self.repeat_timer = threading.Timer(
                self.loop_timer.total_seconds(), self.repeating_start
            )
            self.repeat_timer.start()
