from typing import Any, Iterable, NoReturn
import json

from websockets.sync.connection import Connection

from .exceptions import ProtocolError, GameEnd


# We only support a few known errors to avoid arbitrary calls
ERRORS = {
    e.__name__: e for e in (ValueError, TypeError, KeyError, ProtocolError, GameEnd)
}


def pack(
    payload: "dict[str, Any] | None" = None, error: "Exception | None" = None
) -> str:
    """Pack an error or payload into a message"""
    if error is not None:
        assert not payload, "message payload is ignored if 'error' is given"
        return json.dumps(
            [{}, {"exc_type": type(error).__name__, "exc_args": error.args}]
        )
    elif payload is not None:
        return json.dumps([payload or {}, {}])
    else:
        raise ValueError("one of 'error' or 'payload' must be given")


def unpack(_msg: str) -> "dict[str, Any]":
    """Unpack a received message, returning the payload or raising the error"""
    payload, error = json.loads(_msg)
    if error:
        raise ERRORS[error["exc_type"]](*error["exc_args"])
    return payload  # type: ignore


def read_keys(payload: "dict[str, Any]", keys: "tuple[str, ...]") -> "Iterable[Any]":
    """Unpack the ``keys`` of an unpacked ``payload``"""
    try:
        return [payload[key] for key in keys]
    except KeyError as ke:
        raise ProtocolError(f"missing reply field {ke.args[0]!r}") from ke


def unpack_keys(_msg: str, keys: "tuple[str, ...]") -> "Iterable[Any]":
    """Convenience function to :py:func:`~.unpack` and :py:func:`~.read_keys`"""
    payload = unpack(_msg)
    return read_keys(payload, keys)


def communicate(_ws: Connection, *keys: str, **payload: Any) -> "Iterable[Any]":
    """Send a message ``payload`` and return the reply ``keys`` values"""
    _ws.send(pack(payload))
    return unpack_keys(_ws.recv(), keys)  # type: ignore[arg-type]


def fail(_ws: Connection, error: Exception) -> NoReturn:
    """Fail communication with ``error``, passing it on and raising it locally"""
    _ws.send(pack(error=error))
    raise error
