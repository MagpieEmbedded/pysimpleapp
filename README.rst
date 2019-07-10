===========
pysimpleapp
===========


.. image:: https://img.shields.io/pypi/v/pysimpleapp.svg
        :target: https://pypi.python.org/pypi/pysimpleapp

.. image:: https://img.shields.io/travis/MagpieEmbedded/pysimpleapp.svg
        :target: https://travis-ci.org/MagpieEmbedded/pysimpleapp

.. image:: https://readthedocs.org/projects/pysimpleapp/badge/?version=latest
        :target: https://pysimpleapp.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Simple framework for applications in python

Aims
----

This package is intended to provide the basic components for applications in Python.
It provides a white box implementation of multi threaded applications.

**pysimpleapp** welcomes additional base classes and implementations of application methodologies.

There is often more than one way to do something and **pysimpleapp** tries to support
that by providing building blocks rather than solutions.

It is intended to be GUI framework agnostic, although some common frameworks have been included for demonstration and ease of use.

There should also be a relatively thorough set of tutorials alongside the main code.
This will teach how to use the software and explain why the software is this way.


* Source code: https://github.com/MagpieEmbedded/pysimpleapp
* Documentation: https://pysimpleapp.readthedocs.io.
* Free software: MIT license

Installation
------------

**pysimpleapp** is hosted on `PyPi <https://pypi.org/project/pysimpleapp//>`_ so can be installed with:

.. code-block bash

        pip install pysimpleapp

Simple Examples
---------------

Below are some simple examples which have been prepared.

To understand how they work and how to build more complex applications, please visit the **tutorials** section of the documentation.

Threads
^^^^^^^

Open a python session with **pysimpleapp** installed.

Import libraries and classes:

.. code-block:: python

        from pysimpleapp.message import Message
        from pysimpleapp.threads.examples import ExampleSingleRunThread, ExampleMultiRunThread
        from queue import Queue
        from threading import Thread

Threads take a name as the first argument, owner name as the second argument and an input and
output queue for communication.
Their use will be demonstrated shortly but you can confirm that they inherit from the
`threading.Thread <https://docs.python.org/3/library/threading.html#thread-objects.>`_ class.

Let's create the input and output queues and an instance of the ExampleSingleRunThread class:

.. code-block:: python

        in_queue = Queue()
        out_queue = Queue()
        single_run = ExampleSingleRunThread('Name', 'Owner', in_queue, out_queue)
        isinstance(single_run, Thread) # returns True

Now, send the singe_run thread a start command.
Threads in **pysimpleapp** often have some built in commands, but it is very easy to override these and add your own later.

It is also essential to define how you want a thread to behave through it's *main* function.
The ExampleSingleRunThread has been defined to print that it has run.

Put a start message in the input queue:

.. code-block:: python

        # Note the order of owner and name because we are sending from the owner
        in_queue.put(Message('Owner', 'Name', 'THREAD_START', None))
        
This should print: ::

        Running single run thread...

demonstrating that the thread has run!

You will also notice that if you send another start command, nothing happens.
Single Run Threads execute once and then stop.

Next, make an instance of ExampleMultiRunThread:

.. code-block:: python

        multi_run = ExampleMultiRunThread('Name2', 'Owner', in_queue, out_queue)

Multi Run Threads will run until they are told to end.
Test that functionality by providing several messages:

.. code-block:: python

        in_queue.put(Message('Owner', 'Name2', 'THREAD_START', None))
        in_queue.put(Message('Owner', 'Name2', 'THREAD_START', None))
        in_queue.put(Message('Owner', 'Name2', 'THREAD_START', None))

You will see that the thread has been counting how many times you asked it to run!

End the thread with another built in command:

.. code-block:: python

        in_queue.put(Message('Owner', 'Name2', 'THREAD_END', None))

After this, the thread has stopped and will no longer respond to messages.

This has been a very short introduction to some example threds but there is much more to come!
Continue learning with the **tutorials** and soon you will be making your own threads for specific requirements.

Features
--------

* TODO
* Attempt to implement best practices
* Documentation and tutorials

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
