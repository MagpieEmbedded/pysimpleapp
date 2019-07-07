"""
Module with subclasses of threading module which have been
altered to fit within the pysimpleapp system

Threads should have the ability to be started and stopped on command
They should also have parameters which can be set before the thread
is run
"""

import threading
from typing import List
from queue import Queue
import logging
from pysimpleapp import Message


class MultiRunThread(threading.Thread):
    """
    Template thread which executes its *main* function many times.
    Can take start, end commands as well as updating parameters.

    Must be provided with a name, owner, input and output queues.

    The operation of the thread is implemented in *main()*
    This function should be overridden during implementation.

    Parameters are created in *create_params()* which should be overridden when implemented.
    Parameters should not be created from anywhere else.
    Updates to the parameter will be collected after each run of the *main* function.

    Custom message handling may be provided by overriding *custom_handler* as described below.
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

        # Create control flags
        self.start_flag = threading.Event()
        self.end_flag = threading.Event()

        # Create parameters and store a copy in latest_parameters to capture updates
        self.parameters = {}
        self._create_params()
        self.latest_parameters = self.paramaters

    def main(self):
        """
        Override this function to provide the thread with instructions.
        
        This function will be called when the thread has received a THREAD_START command, it will run once and then wait for another THREAD_START command

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

    def custom_handler(self, message: Message):
        """
        Override this function to handle custom user messages.
        Expect a *pysimpleapp.Message* object as an input, no return value is expected or handled by default

        **Good idea:**
        Include a command as a key in a package dictionary to reliably handle custom messages.
        This will be much clearer than sorting by type, size or looking for a specific key or list value.
        """
        pass

    def __update_params(self, new_params: dict):
        """
        Update parameters with new values if the parameter is available.
        Store in *latest_params* which will be copied to *paramaters* at the next available point.

        If the parameter is not found, this will be recorded in the log as an error but will not crash the thread.
        
        :param new_params: Dictionary with one or more parameters to update.
        Must already have been created in *_create_params"
        """
        for key, value in new_params:
            if key in self.paramaters.iterkeys():
                self.latest_parameters[key] = value
            else:
                self.logger.error(
                    f"Could not find {key} parameter in parameters for thread {self.name}"
                )

    def __message_handle(self, message: Message):
        """Handle incoming messages.

        Expects messages to *pysimpleapp.Message* objects

        Checks that message is addressed to itself, by name, then runs command.
        Available commands:
            * THREAD_START - will instruct the thread to run
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

        # Handle the message
        if message.command == "THREAD_START":
            self.start_flag.set()
        elif message.command == "THREAD_END":
            self.end_flag.set()
        elif message.command == "THREAD_UPDATE":
            self.__update_params(message.package)
        elif message.command == "THREAD_HANDLE":
            try:
                self.custom_handler(message.package)
            except Exception:
                self.logger.exception(
                    f"Custom handler raised error when handling: {message}"
                )

        return

    def run(self):
        """
        This defines the programatic flow for the thread.

        Multi run threads wait for messages on the *input_queue* and then process them.

        If an end command is given, the thread will return **True** and exit, therefore no longer being able to run.

        If a start command is given and no end command is requested, the *main* function will be called.
        While running, the queue will not be processed.

        .. note:: The thread will exit immediately after the THREAD_STOP command has been handled.
        """
        while self.end_flag.is_set() is False:
            # Get message from input queue and handle it
            message = self.input_queue.get()
            self.__message_handle(message)

            # Check whether start flag has been raised
            if self.start_flag.is_set():
                # Clear the flag to prevent running continuously
                self.start_flag.clear()
                try:
                    self.main()
                except Exception:
                    self.logger.exception("Error ocurred in main function")

        # Return true and exit
        return True
