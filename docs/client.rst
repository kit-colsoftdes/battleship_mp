Client Usage
============


.. py:module:: battleship_mp.client
    :synopsis: async contextlib variants

The :py:mod:`battleship_mp.client` library provides
a client API in the form of a single class :py:class:`~.GameSession`.

Usage Outline
-------------

Code to use the client only needs to import the :py:class:`~.GameSession`.

.. code:: python3

    from battleship_mp.client import GameSession

Since a :py:class:`~.GameSession` also represents remote state,
it cannot be directly instantiated without knowing the server/client protocol.
Instead, use :py:meth:`~.GameSession.connect` or :py:meth:`~.GameSession.start`
to create instances.

.. code:: python3

    with GameSession.connect() as session:
        # session is a connected GameSession instance
        # ready for one round of the game
        ...

Afterwards, the session is ready to exchange ship placement
with the opponent's client via :py:meth:`~.GameSession.place_ships`.
Ship placements express size, position and orientation of each ship;
see the method doc for details.

.. code:: python3

    my_ships = [
        (5, (2, 1), True),
        (3, (4, 5), False),
    ]
    enemy_ships = session.place_ships(*my_ships)

The main game phase consists of multiple rounds of exchanging shots.
Each player can either :py:meth:`~.announce_shot` or :py:meth:`~.expect_shot`
and a player can only announce a new shot after the previous one was expected
by the remote player.
This allows for two styles of exchanging shots: simultaneous or alternating.

*simultaneous shots*
    Both players announce their shot before expecting the enemy shot.
    This gives a play style as if players made their move at the same time.

    .. code:: python3

        # exchange shots with the opponent
        my_shot = (..., ...)
        session.announce_shot(my_shot)
        enemy_shot = session.expect_shot()
        # process both shots now

*alternating shots*
    Only one of the players announces their shot and the other expects it.
    This gives a play style of players taking separate turns.

    .. code:: python3

        if my_move:
            my_shot = (..., ...)
            session.announce_shot(my_shot)
            # process my shot now
        else:
            enemy_shot = session.expect_shot()
            # process enemy shot now

    How players swap turns is not enforced.
    For example, players could swap turns after each shot or after each miss.

Once the exchange of shots has lead to the ships of one or both players being sunk,
peers should :py:meth:`~.end_game` and announce the determined winner.
This may be one of the players' identifiers or ``None`` in case of a draw.
**The server validates whether there is a consensus of who won the game.**
In addition, a player may :py:meth:`~.end_game` and ``forfeit`` the game at any time.

Note that the client API – just like the server - generally imposes
little restrictions on the game rules.
If a restriction is not mentioned then the API does not impose it;
for example, there is no restriction on the board size.
Each client should check for itself whether all peers adhere to expected rules.

Class Definition
----------------

.. autoclass:: GameSession
    :members:
