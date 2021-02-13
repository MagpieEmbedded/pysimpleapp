"""Example of screen and thread communicating to flash an "LED" on the screen.
Would be nice to later add a slider to alter the frequency"""

import logging
import threading
import tkinter as tk
from queue import Queue
import time

from pysimpleapp.threads.thread_manager import ThreadManager
from pysimpleapp.screens.tk_screens import TkScreenTemplate, TkScreenManager
from pysimpleapp.threads.simple_threads import PreciseRepeatingThread
from pysimpleapp.message import Message


class FlashScreen(TkScreenTemplate):
    def __init__(
        self, name: str, owner: str, output_queue: Queue, master, quit_command: callable
    ):
        super().__init__(name, owner, output_queue, master, quit_command)
        self.master.title(self.owner)
        # Boolean state for LED
        self.led_on = False
        # Frame acting as LED
        self.led = tk.Frame(self, bg="gray", height=200, width=200)
        self.led.pack(padx=50, pady=50)
        # Label explaining what to do
        self.label = tk.Label(
            self, text="LED will flash when update is received from thread"
        )
        self.label.pack()

    def show(self):
        self.pack()
        # Subscribe to flashing
        print("Subscribing to flashing")
        self.send_to(["Example Manager", "Flash Thread"], "SUBSCRIBE", None)

    def hide(self):
        self.pack_forget()
        # Unsubscribe from flashing
        print("Unsubscribing from flashing")
        self.send_to(["Example Manager", "Flash Thread"], "UNSUBSCRIBE", None)

    def update(self, message: Message):
        if message.command == "FLASH":
            # Invert boolean state
            self.led_on = not self.led_on
            if self.led_on is True:
                self.led.configure(bg="green")
            else:
                self.led.configure(bg="gray")


class FlashThread(PreciseRepeatingThread):
    def create_params(self):
        self.address_book["SUBSCRIBE"] = self.subscribe
        self.address_book["UNSUBSCRIBE"] = self.unsubscribe
        # Set of subscribers to send update to
        self.parameters["subscribers"] = []

    def subscribe(self, message: Message):
        # If the sender is not already subscribed, make it a subscriber
        if message.sender not in self.parameters["subscribers"]:
            self.parameters["subscribers"].append(message.sender)

    def unsubscribe(self, message: Message):
        # If the sender is subscribed then unsubscribe
        if message.sender in self.parameters["subscribers"]:
            self.parameters["subscribers"].remove(message.sender)

    def main(self):
        print("Flashing...")
        for subscriber in self.parameters["subscribers"]:
            print(f"Sending to {subscriber}")
            self.send_to(subscriber, "FLASH", None)


if __name__ == "__main__":

    in_queue = Queue()
    out_queue = Queue()

    manager = "Example Manager"
    screen_manager_1 = "Screen Manager 1"
    screen_manager_2 = "Screen Manager 2"
    owner = "Owner"
    flash_screen = "Flash Screen"
    flash_thread = "Flash Thread"

    print(f"Active Threads: {threading.active_count()}")

    # Create the ThreadManager
    print("Creating Example Manager")
    example_manager = ThreadManager(manager, owner, in_queue, out_queue)
    print(f"Active Threads: {threading.active_count()}")

    # Supply a dictionary of thread types
    print("Providing thread types")
    in_queue.put(
        Message(
            owner,
            [manager],
            "SET_THREAD_TYPES",
            {"SCREEN": TkScreenManager, "FLASH_THREAD": FlashThread},
        )
    )

    # Create Threads
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": screen_manager_1, "thread_type": "SCREEN"},
        )
    )
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": screen_manager_2, "thread_type": "SCREEN"},
        )
    )
    in_queue.put(
        Message(
            owner,
            [manager],
            "NEW_THREAD",
            {"thread_name": flash_thread, "thread_type": "FLASH_THREAD"},
        )
    )
    time.sleep(0.1)
    print(f"Active Threads: {threading.active_count()}")

    print("Add and start Flash Screen on both thread managers")
    in_queue.put(Message(owner, [manager, screen_manager_1], "THREAD_START", None))
    in_queue.put(
        Message(
            owner,
            [manager, screen_manager_1],
            "NEW_SCREEN",
            {"screen_name": flash_screen, "screen_type": FlashScreen},
        )
    )
    in_queue.put(
        Message("owner", [manager, screen_manager_1], "SHOW_SCREEN", flash_screen)
    )
    in_queue.put(Message(owner, [manager, screen_manager_2], "THREAD_START", None))
    in_queue.put(
        Message(
            owner,
            [manager, screen_manager_2],
            "NEW_SCREEN",
            {"screen_name": flash_screen, "screen_type": FlashScreen},
        )
    )
    in_queue.put(
        Message("owner", [manager, screen_manager_2], "SHOW_SCREEN", flash_screen)
    )

    print("Starting up flashing thread")
    in_queue.put(Message(owner, [manager, flash_thread], "THREAD_START", None))
    print("Will automatically quit in 30 seconds")
    time.sleep(30)
    in_queue.put(Message(owner, [manager], "THREAD_END", None))
