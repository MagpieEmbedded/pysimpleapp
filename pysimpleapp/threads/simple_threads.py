"""
Module with subclasses of threading module which have been
altered to fit within the pysimpleapp system.

Threads should have the ability to be started and stopped on command
They should also have parameters which can be set before the thread
is run.
"""

import threading
from typing import List
from queue import Queue
import logging
from pysimpleapp.message import Message
import time
from abc import ABC, abstractclassmethod


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

    def __init__(
        self, name: str, owner: List[str], input_queue: Queue, output_queue: Queue
    ):
        """
        Create the thread, set up control flags and call _create_params

        :param name: Identifier for the thread, could be list of strings depending on communication model
        :param owner: Address of object which asked for this thread to be created
        :param input_queue: Input pipe for messages which the thread is expected to process
        :param output_queue: Output pipe for messages which should be sent elsewhere
        """
        # Create thread
        super().__init__(name=name)
        # Set attributes
        self.owner = owner
        self.input_queue = input_queue
        self.output_queue = output_queue

        # Give the logger name of the thread for debugging
        self.logger = logging.getLogger(self.name)

        # Create control flags - some of these are for use in more complex threads
        self.start_flag = threading.Event()
        self.stop_flag = threading.Event()
        self.reset_flag = threading.Event()
        self.end_flag = threading.Event()

        # Create parameters
        self.parameters = {}
        self.create_params()

        # Set up address book
        self.address_book = {
            "THREAD_START": self.__thread_start,
            "THREAD_STOP": self.__thread_stop,
            "THREAD_END": self.__thread_end,
            "THREAD_UPDATE": self._update_params,
            "THEAD_HANDLE": self.custom_handler,
        }

        # Start thread object
        self.start()

    @abstractclassmethod
    def main(self):
        """
        Override this function to provide the thread with instructions.
        
        *main* provides the functionality for the thread.
        It may contain heavy computations, IO processing and anything you want to do without having to worry about
        *exactly* how long it takes.

        **Good ideas:**

        * Read from parameters to decide on program execution
        * Send *pysimpleapp.Message* objects out through the *output_queue* with feedback and information
        * Handle exceptions to prevent unnecessary failures of the thread

        **Bad ideas:**

        * Writing to parameters *during* program execution
        * Writing things back to the *input_queue*
        * Implementing operations which take a long time to complete and expecting fast reactions in changes to parameters or THREAD_STOP commands
        """
        pass

    @abstractclassmethod
    def create_params(self):
        """
        Override this function to add parameters.
        This should be the only method used to create parameters in a thread.
        Example:

        .. code-block:: python

            self.parameters["param 1"] = 0
            self.parameters["param 2"] = "some string"

        """
        pass

    def __thread_start(self, message: Message):
        """Handle a start message by setting the start flag"""
        self.start_flag.set()

    def __thread_stop(self, message: Message):
        """Handle a stop message by setting the stop flag"""
        self.stop_flag.set()

    def __thread_end(self, message: Message):
        self.end_flag.set()

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

        for key, value in new_params:
            if key in self.paramaters.iterkeys():
                self.parameters[key] = value
            else:
                self.logger.error(
                    f"Could not find {key} parameter in parameters for thread {self.name}"
                )

    def _message_handle(self, message: Message):
        """Handle incoming messages.

        Expects messages to *pysimpleapp.Message* objects

        Checks that message is addressed to itself, by name, then runs command.
        Available commands:
            * THREAD_START - will instruct the thread to run
            * THREAD_STOP - will instruct the thread to stop
            * THREAD_END - will instruct the thread to end
            * THREAD_UPDATE - will instruct the thread to update parameters from the attached package
            * THREAD_HANDLE - calls the custom_handler function with the package as input
        Sending another command will be recorded as an error but will not crash the thread
        
        :params message: A *pysimpleapp.Message* object to process
        """
        # Sanity check that this is the thread meant to be receiving this message
        try:
            assert message.receiver == self.name
        except AssertionError:
            self.logger.error(
                f"Expected message for {self.name}, got message for {message.receiver}\n"
                f"Message contents: {message}"
            )
            # Leave
            return
        # Try to execute the command specified in the address book, otherwise make a note that it didn't work
        try:
            self.address_book[message.command](message)
        except KeyError:
            logging.error(
                f"Expected command in {self.address_book.iterkeys()}, got {message.command} in message: {message}"
            )

        return

    @abstractclassmethod
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
            message = self.input_queue.get()
            self._message_handle(message)

            # Check whether start flag has been raised
            if self.start_flag.is_set():
                # Clear the flag to prevent running continuously
                self.start_flag.clear()
                try:
                    self._control_loop()
                except Exception:
                    self.logger.exception("Error ocurred in main function")
                    # Exit gracefully
                    self.end_flag.set()

        # Return true and exit
        return True


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

    def __init__(
        self, name: str, owner: List[str], input_queue: Queue, output_queue: Queue
    ):
        super().__init__(name, owner, input_queue, output_queue)
        self.parameters["loop_timer"] = 1

    def repeating_start(self):
        """Command to set the *main* function going again"""
        self.input_queue.put(Message(self.name, self.name, "THREAD_START", None))

    def _control_loop(self):
        """Run the main function and set a timer on sending a new start command, unless the stop flag is raised."""
        if self.stop_flag.is_set():
            self.stop_flag.clear()
        else:
            self.main()
            threading.Timer(self.parameters["loop_timer"], self.repeating_start).start()
