Player Adapter
==============

The :py:class:`~.GameSession` client API closely mimics how an individual player
would operate and which information they would need during a session.
Thus, for client programs that already have a ``class Player`` abstraction,
the client API can be integrated via the `Adapter Pattern`_ by implementing
a new kind of ``Player`` as an adapter to the :py:class:`~.GameSession`.

.. note::

    It is important to distinguish between "the player" as a human being
    *using* the client program and "the ``Player``" as an abstraction as
    *part of*  the client program.
    Keep in mind that "the ``Player``" needs access to more information
    than "the player";
    this becomes apparent when wrapping a :py:class:`~.GameSession`,
    since it means explicitly giving "the ``Player``" information
    about its opponent.

Since the adapter ``Player`` needs access to information that is usually
communicated implicitly – for example, the ship positions shown via the UI
or even the length of a session – it is very likely necessary to extend the
``Player`` abstraction to match.
The following is an outline of how such an adapter can be designed.

For simplicity, this outline only assumes
one "local" player directly using the client program, and
one "remote" player connected via the :py:class:`~.GameSession`.
You likely still want to support local vs local play,
and might want to support remote vs remote play as well.

Creating Instances
------------------

A :py:class:`~.GameSession` needs to be scoped to one round of the game
and can only disclose the opponent player name after connecting to a game.
This prevents just constructing a ``RemotePlayer`` that wraps the session.

We recommend to extend the ``Player`` abstraction with:

- an alternative constructor via :py:func:`classmethod` which is
- scoped to one round of the game via :py:func:`~contextlib.contextmanager`.

.. code:: python3

    class RemotePlayer:
        # this constructor usually is not called manually:
        # 'identifier' is provided by the player on the remote session!
        def __init__(self, identifier: str, session: GameSession):
            self.identifier = identifier
            self._session = session

        @classmethod
        @contextmanager
        def create(cls, opponent: "str | None"):
            """
            Create a scoped instance of this class and inform it of its ``opponent``
            """
            # 'opponent' is the local player, 'session.opponent' the remote player
            with GameSession.connect(opponent) as session:
                yield cls(session.opponent, session)

The constructor can then be used in a `with statement`_:

.. code:: python3

    with RemotePlayer.create(...) as player:
        ...

Note that you can create two players of type ``P1`` and ``P2``
in one ``with`` statement using
``with P1.create(...) as player1, P2.create(...) as player2:``.

.. warning::

    The ``opponent`` identifier is sent to whichever player is matched by the server
    without any authentication.
    Avoid exposing any personal information such as the account- or hostname
    (e.g. by creating an ``f"{opponent}@{hostname}"`` identifier).
    When in doubt, do not provide any identifier - the client API will then
    create a random one that exposes no information.

Wrapping Methods
----------------

The methods of :py:class:`~.GameSession` are unlikely to
directly match ``Player`` methods.
At the very least, you must *delegate* method calls:

.. code:: python3

    class RemotePlayer:
        ...

        def get_shot(self):
            return self._session.expect_shot()

In addition, expect to *adapt* method calls:

.. code:: python3

    class RemotePlayer:
        ...

        def notify_shot(self, x, y):
            # adapt the different parameter convention
            return self._session.announce_shot((y, x))

When expected and provided methods are very different,
be prepared to implement a *facade* between both conventions:

.. code:: python3

    class RemotePlayer:
        def __init__(self, ...):
            ...
            # translate between individual and all-at-once placements
            # by storing them internally
            self._enemy_ship_buffer: "list[SHIP_PLACEMENT] | None" = []
            self._my_ship_buffer: "list[SHIP_PLACEMENT] | None" = None

        def notify_ship(self, size: int, pos: "tuple[int, int]", vertical: bool):
            """Inform about enemy placing a ship of specific `size` at `pos`"""
            # keep collecting all ship placements without sending any
            self._enemy_ship_cache.append((size, pos, vertical))

        def get_ship(self, size: int) -> "SHIP_PLACEMENT":
            """Get the next placement for a ship of specific `size`"""
            # send ship placement only when we need the response
            if self._my_ship_buffer is None:
                self._my_ship_buffer = list(
                    session.place_ships(*self._enemy_ship_cache)
                )
                self._enemy_ship_cache = None
            # pick matching ship from collection provided from remote
            for idx, (candidate_size, _, _) in enumerate(self._my_ship_buffer):
                if size == candidate_size:
                    return self._my_ship_buffer.pop(idx)
            raise ValueError(f"remote player placed no more ships of size {size}")

.. _Adapter Pattern: https://en.wikipedia.org/wiki/Adapter_pattern
.. _with statement: https://docs.python.org/3/reference/compound_stmts.html#the-with-statement