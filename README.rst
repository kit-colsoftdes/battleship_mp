##########################################################
``battleship_mp`` - Multiplayer Support for CSD Battleship
##########################################################

This package provides a simple client and server for the Battleship game.
It tries to be roughly compatible with the Collaborative Software Design implementation.
Behind the scenes, it uses `WebSocket`_ for communication between client and server.

Client Usage
------------

Set the environment variable ``BMP_SERVER_URL`` to the server's websocket URL.
For example, if the server runs locally on port ``8765``
then use ``BMP_SERVER_URL="ws://localhost:8765"`` before starting the program.
Alternatively, this can also be set inside Python by using
``os.environ["BMP_SERVER_URL"] = "ws://localhost:8765"``.

The entire client functionality is encapsulated by ``battleship_mp.client.GameSession``.
This allows to join a game, transmit a board of set ships, and exchange shots.
Note that the server does **not** perform any notable game state evaluation;
multiplayer peers **must** exchange their game state (notably, their entire game board)
to locally check the game progress.

Installation
------------

You can install the package directly from the repository;
only Python >= 3.7 is required.
Using a `venv`_ is strongly recommended!

.. code:: bash

    ~ $ git clone https://git.scc.kit.edu/collabsoftwaredesign-2023/battleship_mp.git
    Cloning into 'battleship_mp'...
    ...
    ~ $ python3 -m venv venv
    ~ $ source venv/bin/activate
    (venv) ~ $ python3 -m pip install ./battleship_mp
    Processing path/to/repo
        ...
    Successfully installed battleship_mp-1.0.0

**Note**:
If you want to develop in the repo, also pass the ``-e`` flag to pip.
This allows you to make changes without having to re-install the package.

.. _WebSocket: https://en.wikipedia.org/wiki/WebSocket
.. _venv: https://docs.python.org/3/library/venv.html