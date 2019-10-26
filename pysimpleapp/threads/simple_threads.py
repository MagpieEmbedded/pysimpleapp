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

    def __init__(self, name: str, owner: str, input_queue: Queue, output_queue: Queue):
        """
        Create the thread, set up control flags and call _create_params

        :param name: Identifier for the thread, could be list of strings depending on communication model
        :param owner: Address of object which created the thread (often a ThreadManager)
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
        self.logger = logging.getLogger(f"{type(self).__name__}-{self.name}")

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
            "THREAD_START": self._thread_start,
            "THREAD_STOP": self._thread_stop,
            "THREAD_END": self._thread_end,
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

    def _thread_start(self, message: Message):
        """Handle a start message by setting the start flag"""
        self.start_flag.set()

    def _thread_stop(self, message: Message):
        """Handle a stop message by setting the stop flag"""
        self.stop_flag.set()

    def _thread_end(self, message: Message):
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
        # Log the message
        self.logger.debug(
            f"MESSAGE Sender: {message.sender}, Command {message.command}, Package: {message.package}"
        )

        # Sanity check that this is the thread meant to be receiving this message
        try:
            assert message.receiver == self.name or message.receiver == [self.name]
        except AssertionError:
            self.logger.error(
                f"Expected message for {self.name}, got message for {message.receiver}\n"
            )
            # Leave
            return
        # Try to execute the command specified in the address book, otherwise make a note that it didn't work
        try:
            self.address_book[message.command](message)
        except KeyError:
            logging.error(
                f"Expected command in {self.address_book.keys()}, got {message.command} in message: {message}"
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

    def __init__(self, name: str, owner: str, input_queue: Queue, output_queue: Queue):
        super().__init__(name, owner, input_queue, output_queue)
        # Add loop timer parameter to describe how often function should run
        self.parameters["loop_timer"] = 1
        # Add repeat function to address book
        self.address_book["THREAD_REPEAT"] = self._thread_repeat
        # Hold onto the current timer to cancel if necessary
        self.repeat_timer = None

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
        if self.repeat_timer:
            self.repeat_timer.cancel()

    def _thread_stop(self, message: Message):
        """Raise the stop flag and cancel the current timer"""
        self.stop_flag.set()
        if self.repeat_timer:
            self.repeat_timer.cancel()

    def repeating_start(self):
        """Command to set the *main* function going again"""
        self.input_queue.put(Message(self.name, self.name, "THREAD_REPEAT", None))

    def _control_loop(self):
        """Run the main function and set a timer on sending a new start command, unless the stop flag is raised."""
        if not self.stop_flag.is_set():
            self.main()
            self.repeat_timer = threading.Timer(
                self.parameters["loop_timer"], self.repeating_start
            )
            self.repeat_timer.start()


class PreciseRepeatingThread(RepeatingThread):
    """
    Like the repeating thread but with more of an emphasis on getting the timing exactly right.

    Use command "SET_LOOP_TIMER" with a package of {"loop_timer": $time} to ensure changes are handled properly.

    Subtracts the amount of time taken for the *main* function exection from the time to wait until the
    next call.
    Use this if there is a function for which regularity is important but functionality can
    occasionally be slow.
    
    If main execution takes longer than loop_timer, an error message will be logged.
    """

    def __init__(self, name, owner, input_queue: Queue, output_queue: Queue):
        super().__init__(name, owner, input_queue, output_queue)
        # Initialize started time and count on number of main runs
        self.started_time = 0.0
        self.main_runs = 0
        # Set flag for basing predictions
        self.new_predictions_flag = threading.Event()
        # Add loop timer instruction to address book
        self.address_book["SET_LOOP_TIMER"] = self.set_loop_timer

    def set_loop_timer(self, message: Message):
        """Update the loop timer parameter and raise flag to start measuring from a new point"""
        try:
            assert type(message.package) == dict
            assert "loop_timer" in message.package.keys()
            self._update_params(message)
            self.new_predictions_flag.set()
        except AssertionError:
            logging.error(
                f"Expected 'loop_timer' in dict for loop timer, got {type(message.package)}"
            )

    def _thread_repeat(self, message: Message):
        """Do nothing"""
        pass

    def _thread_start(self, message: Message):
        """Set the start flag and also record the time at which a new start was commanded"""
        super()._thread_start(message)
        self.new_predictions_flag.set()

    def repeating_start(self):
        """Set the start flag and put an event in the queue to trigger a run"""
        self.start_flag.set()
        self.input_queue.put(Message(self.name, self.name, "THREAD_REPEAT", None))

    def _control_loop(self):
        """
        Get a start time, run the main function and set a timer for as close to the timer_loop as possible.
        
        If the main loop took longer than the timer_loop period, raise a TimeoutError to be logged and handled in *run*.
        """
        if not self.stop_flag.is_set():
            main_start_time = time.time()
            self.main()
            # Bigger of 0 or loop_timer minus the time taken for main to execute, adding the difference between
            # the time the thread should be at after this many runs vs where it actually is
            main_finish_time = time.time()
            # Only for when a new loop_timer is set
            if self.new_predictions_flag.is_set():
                self.started_time = main_start_time
                self.main_runs = 0
                self.new_predictions_flag.clear()
            repeat_time = max(
                [
                    0.0,
                    (
                        self.parameters["loop_timer"]
                        - (main_finish_time - main_start_time)
                        + (
                            (
                                self.parameters["loop_timer"] * self.main_runs
                                + self.started_time
                                - main_start_time
                            )
                        )
                    ),
                ]
            )
            # print(repeat_time)
            self.repeat_timer = threading.Timer(repeat_time, self.repeating_start)
            self.repeat_timer.start()
            # Count runs of main function
            self.main_runs += 1
            # Log that an error ocurred
            if repeat_time == 0.0:
                raise TimeoutError

    def run(self):
        """Change the run function to give priority to a main call"""
        while self.end_flag.is_set() is False:
            # Check whether start flag has been raised
            if self.start_flag.is_set():
                # Clear the flag to prevent running continuously
                self.start_flag.clear()
                try:
                    self._control_loop()
                except TimeoutError:
                    self.logger.error(
                        f"Main function took longer than loop_timer of {self.parameters['loop_timer']} to execute"
                    )
                except Exception:
                    self.logger.exception("Error ocurred in main function")
                    # Exit gracefully
                    self.end_flag.set()

            # Get message from input queue and handle it
            message = self.input_queue.get()
            self._message_handle(message)

        # Return true and exit
        return True
