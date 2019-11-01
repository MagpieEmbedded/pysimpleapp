"""
Screen Manager and template for the Tkinter GUI Library.

Screen Manager to run the Tk mainloop, open and close screens and handle messaging.
Creates it's own Tk instance and has unique access to the root.destroy() function.
Also holds some state values for use across multiple screens and safe method for
accessing this.

Screen Template provides the basic building block for a screen.
"""

import threading
from queue import Queue
import tkinter as tk
import time

from pysimpleapp.threads.simple_threads import SingleRunThread, RepeatingThread
from pysimpleapp.message import Message


class MyFirstGUI:
    def __init__(self, master, msg, quit_command):
        self.master = master
        self.master.geometry("500x500")
        self.master.title("A simple GUI")
        self.message = msg

        self.label = tk.Label(master, text="This is our first GUI!")
        self.label.pack()

        self.greet_button = tk.Button(master, text="Greet", command=self.greet)
        self.greet_button.pack()

        self.close_button = tk.Button(master, text="Close", command=quit_command)
        self.close_button.pack()

    def greet(self):
        print(self.message)


class Screen(RepeatingThread):
    def __init__(self, name: str, owner: str, input_queue: Queue, output_queue: Queue):
        super().__init__(name, owner, input_queue, output_queue)
        self.parameters["loop_timer"] = 0.05
        self.root = None

    def create_params(self):
        pass

    def run(self):
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_command)
        MyFirstGUI(self.root, f"Hello from {self.name}", self.quit_command)
        super().run()

    def quit_command(self):
        self._thread_end(Message(None, None, None, None))

    def _thread_end(self, message: Message):
        self.root.destroy()
        super()._thread_end(message)

    def main(self):
        # print("Updating screen...")
        self.root.update()


inq1 = Queue()
inq2 = Queue()
outq1 = Queue()
outq2 = Queue()

print("Running Tk1 & Tk2")
Tk1 = Screen("Screen 1", "owner", inq1, outq1)
Tk2 = Screen("Screen 2", "owner", inq2, outq2)

Tk1.input_queue.put(Message("owner", "Screen 1", "THREAD_START", None))


time.sleep(10)
Tk2.input_queue.put(Message("owner", "Screen 2", "THREAD_START", None))
