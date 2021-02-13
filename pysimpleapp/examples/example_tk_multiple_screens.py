import tkinter as tk
from queue import Queue
import time

from pysimpleapp.screens.tk_screens import TkScreenTemplate, TkScreenManager
from pysimpleapp.message import Message


class BlueScreen(TkScreenTemplate):
    def __init__(
        self, name: str, owner: str, output_queue: Queue, master, quit_command: callable
    ):
        super().__init__(name, owner, output_queue, master, quit_command)
        self.configure(bg="blue", height=100, width=100)

    def show(self):
        print("Show Blue screen")
        self.pack(side="left")

    def hide(self):
        print("Hide Blue screen")
        self.pack_forget()

    def update(self, message: Message):
        pass


class RedScreen(TkScreenTemplate):
    def __init__(
        self, name: str, owner: str, output_queue: Queue, master, quit_command: callable
    ):
        super().__init__(name, owner, output_queue, master, quit_command)
        self.configure(bg="red", height=100, width=100)

    def show(self):
        print("Show Red screen")
        self.pack(side="right")

    def hide(self):
        print("Hide Red screen")
        self.pack_forget()

    def update(self, message: Message):
        pass


class ChoiceScreen(TkScreenTemplate):
    def __init__(
        self, name: str, owner: str, output_queue: Queue, master, quit_command: callable
    ):
        super().__init__(name, owner, output_queue, master, quit_command)

        self.show_blue_button = tk.Button(
            self, text="Show Blue", command=self.show_blue
        )
        self.show_blue_button.pack(side="left")

        self.hide_blue_button = tk.Button(
            self, text="Hide Blue", command=self.hide_blue
        )
        self.hide_blue_button.pack(side="left")

        self.show_red_button = tk.Button(self, text="Show Red", command=self.show_red)
        self.show_red_button.pack(side="right")

        self.hide_red_button = tk.Button(self, text="Hide Red", command=self.hide_red)
        self.hide_red_button.pack(side="right")

    def show_red(self):
        self.send_to([self.owner], "SHOW_SCREEN", "Red")

    def hide_red(self):
        self.send_to([self.owner], "HIDE_SCREEN", "Red")

    def show_blue(self):
        self.send_to([self.owner], "SHOW_SCREEN", "Blue")

    def hide_blue(self):
        self.send_to([self.owner], "HIDE_SCREEN", "Blue")

    def show(self):
        print("Show Choice screen")
        self.pack(side="bottom")

    def hide(self):
        print("Hide Choice screen")
        self.pack_forget

    def update(self, message: Message):
        pass


if __name__ == "__main__":

    inq1 = Queue()
    outq1 = Queue()

    Manager = "Screen Manager"
    choice_screen = "Choice"
    blue_screen = "Blue"
    red_screen = "Red"

    print("Running Tk Screen Manager")
    Tk1 = TkScreenManager(Manager, "owner", inq1, outq1)

    Tk1.input_queue.put(Message("owner", [Manager], "THREAD_START", None))
    Tk1.input_queue.put(
        Message(
            "owner",
            [Manager],
            "NEW_SCREEN",
            {"screen_name": choice_screen, "screen_type": ChoiceScreen},
        )
    )
    Tk1.input_queue.put(
        Message(
            "owner",
            [Manager],
            "NEW_SCREEN",
            {"screen_name": blue_screen, "screen_type": BlueScreen},
        )
    )
    Tk1.input_queue.put(
        Message(
            "owner",
            [Manager],
            "NEW_SCREEN",
            {"screen_name": red_screen, "screen_type": RedScreen},
        )
    )

    Tk1.input_queue.put(Message("owner", [Manager], "SHOW_SCREEN", choice_screen))
    Tk1.input_queue.put(Message("owner", [Manager], "SHOW_SCREEN", blue_screen))
    Tk1.input_queue.put(Message("owner", [Manager], "SHOW_SCREEN", red_screen))
