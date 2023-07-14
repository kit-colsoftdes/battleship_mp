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

.. _Adapter Pattern: https://en.wikipedia.org/wiki/Adapter_pattern