"""
This module simply contains the message class which will be used to move information around the app
"""

from typing import List


class Message:
    """
    Generic message class which will be used to move information around the system
    """

    def __init__(
        self, sender: List[str], receiver: List[str], command: str, package: any
    ):
        """
        Create the message with data about where the message came from, where it is going, what it should do and any supplementary information.
        The package can be of any type, dictionaries tend to be useful for decoding on the other end.

        :param sender: Address of the object which sent the message
        :param receiver: Address of the intended recipient of the message
        :param command: Headline of the message to allow simple handling
        :param package: Data transferred as part of the message
        """

        self.sender = sender
        self.receiver = receiver
        self.command = command
        self.package = package

    def __str__(self):
        """Provides a human readable output of the message"""
        return f"Sender: {self.sender}, Receiver: {self.receiver}, Command: {self.command}, Package: {self.package}"
