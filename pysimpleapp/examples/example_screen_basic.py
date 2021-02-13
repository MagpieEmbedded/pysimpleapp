import tkinter as tk
from queue import Queue
import time

from pysimpleapp.screens.tk_screens import TkScreenTemplate, TkScreenManager
from pysimpleapp.message import Message


class MyFirstGUI(TkScreenTemplate):
    def __init__(
        self, name: str, owner: str, output_queue: Queue, master, quit_command: callable
    ):
        super().__init__(name, owner, output_queue, master, quit_command)
        self.master.geometry("300x100")
        self.master.title(name)
        self.message = f"Hello from {name}"

        self.label = tk.Label(self, text="This is our first GUI!")
        self.label.pack()

        self.extra_label = tk.Label(self, text="Update this text with 'UPDATE' command")
        self.extra_label.pack()

        self.greet_button = tk.Button(self, text="Greet", command=self.greet)
        self.greet_button.pack()

        self.close_button = tk.Button(self, text="Close", command=quit_command)
        self.close_button.pack()

    def show(self):
        self.pack()

    def hide(self):
        self.pack_forget()

    def greet(self):
        print(self.message)

    def update(self, message: Message):
        # Can assume that message is for this screen as ScreenManager
        # will have processed it properly but may be interested in message
        # metadata such as sender
        if message.command == "UPDATE":
            self.extra_label.configure(text=message.package)


if __name__ == "__main__":

    inq1 = Queue()
    outq1 = Queue()

    Manager = "Screen Manager"
    home_screen = "Screen Manager Example"

    print("Running Tk Screen Manager")
    Tk1 = TkScreenManager(Manager, "owner", inq1, outq1)

    Tk1.input_queue.put(Message("owner", [Manager], "THREAD_START", None))
    Tk1.input_queue.put(
        Message(
            "owner",
            [Manager],
            "NEW_SCREEN",
            {"screen_name": home_screen, "screen_type": MyFirstGUI},
        )
    )
    time.sleep(5)
    Tk1.input_queue.put(Message("owner", [Manager], "SHOW_SCREEN", home_screen))

    time.sleep(5)
    Tk1.input_queue.put(
        Message("owner", [Manager, home_screen], "UPDATE", "Updated with a message!")
    )
