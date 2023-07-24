class ProtocolError(Exception):
    """Exchanged messages did not match the expected protocol"""


class ConnectionClosed(Exception):
    """The client/server connection was closed unexpectedly"""


class GameError(Exception):
    """The shared game entered an erroneous state"""


class Deadlock(GameError):
    """The requested operations by both players would block each other indefinitely"""


class GameEnd(Exception):
    """The game has been ended"""

    def __init__(self, winner: "str | None"):
        super().__init__(winner)
        self.winner = winner
