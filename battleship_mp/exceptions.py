class ProtocolError(Exception):
    """Exchanged messages did not match the expected protocol"""


class GameError(Exception):
    """The shared game entered an erroneous state"""


class Deadlock(GameError):
    """The requested operations by both players would block each other indefinitely"""
