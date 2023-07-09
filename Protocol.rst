##############################
The ``battleship_mp`` Protocol
##############################

The protocol represents each game session as a bi-directional stream of messages.
A websocket is used for the message stream, and messages must be valid JSON.
Each message contains an array of two objects ``[<payload>, <error>]``
though one of these must be empty; a non-empty ``<error>`` indicates an exception.
For simplicity and future compatibility,
only the required fields of the ``<payload>`` are documented
unless a specific ``<error>`` may be expected.

General Notes
#############

Blocking
--------

In general, all steps of the protocol may lead to *blocking*:
after sending a message, the reply may be delayed indefinitely.
In a synchronous implementation of the protocol, e.g. the client,
this leads to blocking calls:
after sending a message the program will pause until the reply is available.

Coordinate System
-----------------

The protocol assumes a (y, x) coordinate system as used by screen indexing.
Given a 10 x 10 board,
(0, 0) is "upper left",
(0, 9) is "upper right",
(9, 0) is "lower left",
and (9, 9) is "lower right".
Consequently, the direction (0, 1) is "horizontal" and (1, 0) is "vertical".

Starting a Session
##################

A session is started by exchanging player details.
This is a single message-reply communication,
with the server determining which players to match and their order.

**Note**:
The order can be ignored for asynchronous play, i.e. both players firing at once.

Message
-------

``identifier: str``
    a human-readable name of the local player

``version: [int, int]``
    protocol version used

Response
--------

``identifier: str``
    the identifier of the matched opponent

``first: bool``
    whether *the opponent* has the first shot

Placing Ships
#############

A started session is prepared by placing ships;
this is done in bulk for all ships, with no regard to individual moves.
This is a single message-reply communication,
with the server exchanging the information once it is available for both players.

Message
-------

``sizes: [int, ...]``
    array of each ship's size

``coords: [[int, int], ...]``
    array of each ship's "upper-left" position

``vertical: [bool, ...]``
    array if each ship is oriented vertically

Response
--------

``sizes: [int, ...]``
    array of each ship's size

``coords: [[int, int], ...]``
    array of each ship's "upper-left" position

``vertical: [bool, ...]``
    array if each ship is oriented vertically

Firing Shots
############

After placing ships, a session allows exchanging shots between the players.
A session may either announce its local player shot or expect the remote player shot.

The protocol does not enforce whether players must swap after each shot,
swap after a miss, or even shoot at the same time.
However, both players must generally be synchronised:
a player is blocked from shooting again before the previous shot is received.

**Note**:
It is a logic error for *both* connected sessions to expect a shot.
The resulting deadlock may-or-may-not be broken by the server.

Firing a shot:

Message
-------

``announce_shot: [int, int]``
    position at which a shot is fired

Response
--------

None.
The client application is expected to check by itself whether the shot hit anything.

Waiting for a shot:

Message
-------

``expect_shot: True``
    the value is discarded

Response
--------

``coord: [int, int]``
    the y, x coordinate which the shot targeted

Checked Firing Shots
####################

TBD

Game End
########

After firing shots, if one peer determines the game has ended it should announce this.
This is a single message-reply communication,
with the server exchanging the information once it is available for both players.

Message
-------

``winner: str | None``
    identifier of the winning player or ``None`` in case of a tie

``forfeit: bool``
    whether the local player forfeits the game

Response
--------

``winner: str | None``
    identifier of the winning player or ``None`` in case of a tie
