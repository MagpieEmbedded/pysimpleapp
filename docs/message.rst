Message
=======

In order to effectively communicate between different parts of the application, all of the components must know what to expect when they get information.
To enable this, messages should be created with the Message class.

This provides a consistent layout for handling messsages throughout the application.
It is set up to be minimal and extendable.
There are also various helper functions to automatically fill in some of these fields in common scenarios.

**sender** and **receiver** are a list of strings, which becomes useful when complex message routing is required.

**command** is simply required to ensure there is a straightforward way to identify different message types when handling messages. 

**package** actually carries the data and may be of any type.
From experience, dictionaries work well.
Adding labels to the data does not add much overhead, but does make the message much easier to parse, allowing for changes in input order, new fields etc.

.. autoclass:: pysimpleapp.message.Message
    :members: __init__

