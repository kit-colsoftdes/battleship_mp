Server Usage
============

The server is a self-contained process to which clients
connect for each session via :py:mod:`websockets`.
To connect, it is sufficient for the client to know
on which address the server is listening.

For testing, we recommend to run the server locally – i.e. on the ``localhost``.
Thus, we use the exemplary address ``ws://localhost:8765`` here.
If the server listens on another host and/or port,
adjust the address appropriately.

Connecting the Client
---------------------

The :py:mod:`battleship_mp.client` module does not need to be passed the server address.
Instead, it reads the address from an `environment variable`_ called ``BMP_SERVER_URL``.

You can easily set the variable when launching your program from the shell:

.. code:: bash

    $ BMP_SERVER_URL="ws://localhost:8765" my_client_program.py

Alternatively, if you program is aware of the server address
– e.g. from the CLI or a configuration file -
it can programmatically modify :py:data:`os.environ`:

.. code:: python3

    import os

    os.environ["BMP_SERVER_URL"] = "ws://localhost:8765"

Running the Server
------------------

The :py:mod:`battleship_mp.server` module provides a self-contained,
asynchronous server implementation.
The server can be run from the command line and takes the port
as well as optionally the addresses or hostnames to bind to.
By default, the server binds to all addresses of its host.

For testing, it is suitable to bind to ``localhost``:

.. code:: bash

    ~ $ python3 -m battleship_mp.server 8765 localhost

.. note::

    The hostnames must correspond to addresses of the host on which the server runs;
    it does not make sense to bind to *other* hosts.
    For example, `localhost`_ usually just corresponds to the local addresses
    ``127.0.0.1`` and ``::1``.

.. _environment variable: https://en.wikipedia.org/wiki/Environment_variable
.. _localhost: https://en.wikipedia.org/wiki/Localhost