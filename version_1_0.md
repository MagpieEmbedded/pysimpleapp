# Version 1.0 Plan

This document describes the set of features which are being worked towards as an initial release.
It also describes features which will explicitly **not** be developed during this effort.

# Key Features

## Simple User Interface

One of the key issues holding the existing `pysimpleapp` work back is that it is hard to use!
All of the messages are sent manually which requires understanding how they all work in order to get anything done.
For this to be a _simple_ application framework we need a clear interface for setting up and running applications.
This will involve numerous helper functions which will package several messages together.
For example, starting or running another thread and subscribing at the same time.

## Simplified Architecture

For 1.0, there will be one top level thread supervisor (currently referred to as manager) which all of the other threads will be controlled by.
This will significantly simplify the setup and closing of the application.
It will also simplify the method by which messages are passed between threads and by which information can be requested about other threads.
This effort to simplify also extends to the thread event loops, and the message types.

## Subscription Endpoints

Threads, particularly long running ones, may have multiple outputs which need to be sent to different places.
Think of a thread which is downloading and parsing multiple files.
One output is the current progress (how many more files left to go), another is data from each file as it comes in, and finally some result which is calculated based on the whole process (total download size for example).
We need a way to allow threads to subscribe to different endpoints, and for threads to send data out through these different endpoints.

## Static Setup

The above features should be supported by allowing the application to be setup with a static configuration.
This will support dynamically creating threads _before_ running the application.
For the user, the top level app file should have roughly this layout:

```python
my_app = App()

my_app.add_thread(...)
...

my_app.run()
```

## Multiple GUI Options

We need to have out of the box support for multiple GUI options.
This essentially requires setting up a simple thread loop which can perform GUI setup, providing an event loop for drawing, and ending threads when the main windows are closed.
Based on the [Python GUI documentation](https://docs.python.org/3/faq/gui.html) we will aim for Tkinter, PyQt/PySide and Kivy support.
Other GUI frameworks can then follow.

# Fail Fast

While the framework is still very much in development, we should default to a fail fast mechanism.
This means if threads raise exceptions which are not explicitly handled, the application should end.
A descriptive error message should be left in the terminal to aid debugging.

# Non Goals

This section includes multiple items which will be a part of future releases, but will not be worked on as part of 1.0.

## Dynamically Create New Threads

This is a feature which may fall out of the architecture designed to achieve the above goals, but for the moment it contains too many complexities.
To expand, some threads may wish to dynamically _create_ new threads _while the application is running_.
What happens if two threads want to create new threads using the same name?
What happens if a thread creates and runs a new thread, then ends it, but tries to create another new thread with the same name before the previous one has closed down?
These are questions which may be answered in time, but we are avoiding the complexity for now.

## Processes

There is only so much which can be gained from threads in Python.
It is natural to wonder how we could include processes, which might allow for more performance demanding tasks to be carried out on a separate core and thereby allow for smoother running.
While we will attempt to use simple features of threads and thread queues which are also supported by their [`multiprocessing`](https://docs.python.org/3/library/multiprocessing.html) counterparts, we will focus only on threads for this release.

## Promises

There are multiple ways of performing asynchronous programming, and one involves `promises`, which can be inserted into otherwise synchronous code.
This may be possible to support in the future using some version of anonymous threads.
However, in order to simplify, we will focus only on supporting designs which use a message passing paradigm.
