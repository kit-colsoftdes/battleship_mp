from typing import Tuple, Generator
from contextlib import contextmanager
import random
import os
from enum import Enum, auto

from websockets.sync.client import connect, Connection  # type: ignore

from . import SERVER_URL_ENV, PROTOCOL_VERSION
from .messages import communicate, fail
from .exceptions import GameError, GameEnd


#: Names used if none is provided
DEFAULT_NAMES = [
    "Dog",
    "Cat",
    "Fox",
    "Quokka",
    "Red Panda",
    "Pika",
    "Capybara",
    "Rabbit",
    "Axolotl",
]


#: Type of ship placement information: size, (y, x), vertical
SHIP_PLACEMENT = Tuple[int, Tuple[int, int], bool]


class State(Enum):
    """Current state of a session to check valid transitions"""

    STARTED = auto()
    PLACED = auto()
    FIRING = auto()
    ENDED = auto()
    FAILED = auto()


class GameSession:
    """
    Handle to an open game session at the server

    As the `opponent` and `first` attributes represent the *remote* player
    they usually cannot be determined locally to create instances.
    Use either of :py:meth:`~.connect` or :py:meth:`~.start` to create instances
    for which these attributes are fetched from the server.

    Since a session represents game state, it must be used in correct order.
    At least the order
    :py:meth:`~.place_ships`
    -> :py:meth:`~.announce_shot` | :py:meth:`~.expect_shot`
    -> ...
    -> :py:meth:`~.announce_shot` | :py:meth:`~.expect_shot`
    -> :py:meth:`~.end_game`
    is enforced.
    Further restrictions may be applied by the peer depending on its game rules.
    """

    def __init__(self, opponent: str, first: bool, connection: Connection):
        #: humanreadable identifier of the opponent
        self.opponent = opponent
        #: whether this player shoots first
        self.first = first
        self._ws = connection
        # rough sanity check if the session is used right
        self._state: State = State.STARTED

    def _check_transition(self, new: State, *expected: State) -> None:
        if self._state not in expected:
            expect_msg = f"{', '.join(e.name for e in expected)} => {new.name}"
            got_msg = f"{self._state.name} => {new.name}"
            self._state = State.FAILED
            fail(
                self._ws,
                GameError(f"{self.opponent} - transition {expect_msg}, not {got_msg}"),
            )
        self._state = new

    @classmethod
    @contextmanager
    def connect(cls, local_name: "None | str") -> "Generator[GameSession, None, None]":
        """
        Create a new session with a new connection to the server

        This creates a new instance based on server information.
        The underlying websocket is managed automatically.
        """
        with connect(os.environ[SERVER_URL_ENV]) as websocket:
            yield cls.start(local_name, websocket)

    @classmethod
    def start(cls, local_name: "None | str", connection: Connection) -> "GameSession":
        """
        Create a new session on an established `connection` to the server

        This creates a new instance based on server information.
        The underlying websocket must be managed manually.
        """
        local_name = (
            local_name
            if local_name is not None
            else f"Anonymous {random.choice(DEFAULT_NAMES)}"
        )
        identifier, first = communicate(
            connection,
            "identifier",
            "first",
            identifier=local_name,
            version=PROTOCOL_VERSION,
        )
        return cls(identifier, first, connection)

    def place_ships(self, *ships: SHIP_PLACEMENT) -> "tuple[SHIP_PLACEMENT, ...]":
        """
        Exchange placement of all the players' ships

        :param ships: placement of the local player's ships
        :returns: placement of the remote player's ships

        Each placement is of the form ``(size, (y, x), vertical)``.
        For example, ``(4, (0, 2), False)`` encodes
        a) a Destroyer of size 4
        b) at the top three cells to the right
        c) oriented to the right.
        """
        self._check_transition(State.PLACED, State.STARTED)
        l_sizes, l_coords, l_vertical = zip(*ships)
        ships = tuple(
            zip(
                *communicate(
                    self._ws,
                    "sizes",
                    "coords",
                    "vertical",
                    sizes=l_sizes,
                    coords=l_coords,
                    vertical=l_vertical,
                )
            )
        )
        return ships

    def announce_shot(self, coord: "tuple[int, int]") -> None:
        """Announce that a shot has been fired"""
        self._check_transition(State.FIRING, State.PLACED, State.FIRING)
        communicate(self._ws, announce_shot=coord)

    def expect_shot(self) -> "tuple[int, int]":
        """Wait for a shot to be fired and return its coordinates"""
        self._check_transition(State.FIRING, State.PLACED, State.FIRING)
        (coord,) = communicate(self._ws, "coord", expect_shot=True)
        return tuple(coord)  # type: ignore

    def end_game(self, winner: "str | None", forfeit: bool = False) -> "str | None":
        """
        End the game, announcing a ``winner`` or ``forfeit``

        Returns the ``winner`` determined by the peer.
        If a game is ``forfeit``, the peer is the winner.
        """
        self._check_transition(State.ENDED, State.PLACED, State.FIRING)
        if forfeit:
            winner = self.opponent
        try:
            communicate(self._ws, "winner", winner=winner, forfeit=forfeit)
        except GameEnd as ge:
            return ge.winner
        else:
            return winner
