"""Some example implementations and runs of the simple_threads"""

import threading
from queue import Queue
import logging
import time
from enum import Enum

from pysimpleapp.threads.simple_threads import (
    SingleRunThread,
    MultiRunThread,
    RepeatingThread,
)
from pysimpleapp.message import Message


class ExampleSingleRunThread(SingleRunThread):
    def setup(self):
        pass

    def main(self):
        print("Running single run thread...")
        self.publish(None)


class ExampleMultiRunThread(MultiRunThread):
    def setup(self):
        self.times_ran = 0

    def main(self):
        self.times_ran += 1
        print(f"Running multi run thread called {self.name} {self.times_ran} times")
        self.publish(self.times_ran)


class ExampleAlternatingThread(MultiRunThread):
    class Endpoints(Enum):
        RESULT = "result"
        NOT_RESULT = "not_result"

    def setup(self):
        self.result = True

    def main(self):
        self.publish(self.result, endpoint=self.Endpoints.RESULT)
        self.publish(not (self.result), endpoint=self.Endpoints.NOT_RESULT)
        self.result = not (self.result)


class ExampleRepeatingThread(RepeatingThread):
    def setup(self):
        self.times_ran = 0

    def main(self):
        self.times_ran += 1
        print(f"Running multi run thread called {self.name} {self.times_ran} times")
        self.publish(self.times_ran)
