"""
Screen Manager and template for the Tkinter GUI Library.

Screen Manager to run the Tk mainloop, open and close screens and handle messaging.
Creates it's own Tk instance and has unique access to the root.destroy() function.
Also holds some state values for use across multiple screens and safe method for
accessing this.

Screen Template provides the basic building block for a screen.
Screens require:
- screen name
- name of owner for sending messages
- master (so they can place themselves in the right frame)
- quit_command in case they need to end the program for some reason

Everything else can be obtained from state

Screens must implement constructor functions with the above parameters, show() and hide()
functions with no parameters and a message_handle function which takes messages.
"""

import threading
from queue import Queue
import tkinter as tk
import time

from pysimpleapp.threads.simple_threads import SingleRunThread, RepeatingThread
from pysimpleapp.message import Message


class MyFirstGUI(tk.Frame):
    def __init__(self, owner: str, name: str, master, quit_command: callable):
        super().__init__(master)
        self.master = master
        self.master.geometry("500x500")
        self.master.title(name)
        self.message = f"Hello from {name}"

        self.label = tk.Label(self, text="This is our first GUI!")
        self.label.pack()

        self.greet_button = tk.Button(self, text="Greet", command=self.greet)
        self.greet_button.pack()

        self.close_button = tk.Button(self, text="Close", command=quit_command)
        self.close_button.pack()

    def show(self):
        self.pack()

    def hide(self):
        self.hide()

    def greet(self):
        print(self.message)


class Screen(RepeatingThread):
    def __init__(self, name: str, owner: str, input_queue: Queue, output_queue: Queue):
        super().__init__(name, owner, input_queue, output_queue)
        # Set loop timer to 10Hz by default for regular screen updates
        self.parameters["loop_timer"] = 0.1
        # Dict of screen names to screen type
        self.screens = {}
        # List of screens which have been shown but not hidden
        self.active_screens = []
        # Provide a default title
        self.title = "Tk Screen Manager"

        # Map functions
        self.address_book["NEW_SCREEN"] = self.new_screen
        self.address_book["SHOW_SCREEN"] = self.show_screen
        self.address_book["HIDE_SCREEN"] = self.hide_screen

    def create_params(self):
        pass

    def quit_command(self):
        # Directly call the end thread function
        self._thread_end(Message(None, None, None, None))

    def new_screen(self, message: Message):
        """Create a new screen and add it to the available screens if the name is not already taken"""
        try:
            screen_name = message.package["screen_name"]
            screen_type = message.package["screen_type"]
        except KeyError:
            self.logger.error(
                f"Could not find screen_name and screen_type in message - {message}"
            )
            return
        if screen_name in self.screens:
            self.logger.error(
                f"Tried to create screen called '{screen_name}' but one  already existed"
            )
            return
        # Instantiate the screen
        # This should later be expanded to allow screens to embed themselves in other screens
        self.screens[screen_name] = screen_type(
            screen_name, self.name, self.root, self.quit_command
        )

    def show_screen(self, message: Message):
        """Check that the screen is available and not already being shown before calling its show command"""
        if message.package not in self.screens:
            self.logger.error(
                f"Could not find screen '{message.package}' in available screens"
            )
            return
        elif message.package in self.active_screens:
            self.logger.error(f"Screen '{message.package}' is already being shown")
            return

        self.screens[message.package].show()

    def hide_screen(self, message: Message):
        """Check that the screen is available and being shown before calling its hide command"""
        if message.package not in self.screens:
            self.logger.error(
                f"Could not find screen '{message.package}' in available screens'"
            )
            return
        elif message.package not in self.active_screens:
            self.logger.error(f"Screen '{message.package}' is already hidden'")
            return

        self.screens[message.package].hide()

    def get_active_screens(self, message: Message):
        """Return a dictionary to the sender of the screens and the name of their screen class"""
        active_screens_dict = {
            screen_name: type(self.screens[screen_name]).__name__
            for screen_name in self.screens.keys()
        }
        self.send_to(message.sender, "ACTIVE_SCREENS", active_screens_dict)

    def _thread_end(self, message: Message):
        # Hide all the screens to give them time to perform any shutdown activities
        for screen in self.active_screens:
            screen.hide()
        #  Destroy the root component
        self.root.destroy()
        # End the thread
        super()._thread_end(message)

    def run(self):
        # Create a new TK instance and then run as a normal repeating thread
        self.root = tk.Tk()
        # Give window default title
        self.root.title(self.title)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_command)
        super().run()

    def main(self):
        # print("Updating screen...")
        self.root.update()


if __name__ == "__main__":

    inq1 = Queue()
    outq1 = Queue()

    print("Running Tk Screen Manager")
    Tk1 = Screen("Screen 1", "owner", inq1, outq1)

    Tk1.input_queue.put(Message("owner", "Screen 1", "THREAD_START", None))
    Tk1.input_queue.put(
        Message(
            "owner",
            "Screen 1",
            "NEW_SCREEN",
            {"screen_name": "home", "screen_type": MyFirstGUI},
        )
    )
    time.sleep(5)
    Tk1.input_queue.put(Message("owner", "Screen 1", "SHOW_SCREEN", "home"))
