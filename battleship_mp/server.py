from typing import Awaitable, NamedTuple, Tuple, Iterable, Any, Sequence
from asyncio import gather, Future, ensure_future, run as run_asyncio
import argparse
import random
import logging

import websockets
from websockets.server import WebSocketServerProtocol

from .messages import pack, unpack, unpack_keys
from .exceptions import Deadlock, GameEnd


logger = logging.getLogger("battleship_mp.server")


def send(_ws: WebSocketServerProtocol, **payload: Any) -> Awaitable[None]:
    return _ws.send(pack(payload))


async def recv(_ws: WebSocketServerProtocol, *keys: str) -> Iterable[Any]:
    return unpack_keys(await _ws.recv(), keys)  # type: ignore[arg-type]


class Client(NamedTuple):
    """A client waiting for matching game"""

    identifier: str
    websocket: WebSocketServerProtocol


class Game:
    def __init__(self, client_a: Client, client_b: Client):
        self.clients = client_a, client_b
        self.task = ensure_future(self.run())
        self.identifier = f"{client_a.identifier!r} vs {client_b.identifier!r}"

    async def run(self) -> None:
        logger.info("run %s", self.identifier)
        try:
            await self.handle_start()
            await self.handle_placement()
            await self.handle_shots()
        except GameEnd as ge:
            logger.info("end %s, winner %s", self.identifier, ge.winner)
        except Exception as exc:
            message = pack(error=exc)
            await gather(
                self.clients[0].websocket.send(message),
                self.clients[1].websocket.send(message),
            )
            logger.exception("abort %s", self.identifier)

    async def handle_start(self) -> None:
        logger.debug("handle_start %s", self.identifier)
        for idx, client in enumerate(self.clients):
            await send(
                client.websocket,
                identifier=self.clients[(idx + 1) % 2].identifier,
                first=(idx == 0),
            )

    async def handle_placement(self) -> None:
        logger.debug("handle_placement %s", self.identifier)
        keys = "sizes", "coords", "vertical"
        ships = await gather(
            recv(self.clients[0].websocket, *keys),
            recv(self.clients[1].websocket, *keys),
        )
        await gather(
            send(self.clients[0].websocket, **dict(zip(keys, ships[1]))),
            send(self.clients[1].websocket, **dict(zip(keys, ships[0]))),
        )

    async def handle_shots(self) -> None:
        logger.debug("handle_shots %s", self.identifier)
        sock_a, sock_b = self.clients[0].websocket, self.clients[1].websocket
        buffer: "tuple[Any, Any]| None" = None
        while True:
            a_action, b_action = map(
                unpack,  # type: ignore[arg-type]
                await gather(sock_a.recv(), sock_b.recv()),
            )
            logger.debug("handle_shots %s, %s, %s", self.identifier, a_action, b_action)
            await self.handle_end(a_action, b_action)
            if "expect_shot" in a_action and "expect_shot" in b_action:
                if buffer is None:
                    message = pack(error=Deadlock("both peers wait for shot"))
                    await gather(sock_a.send(message), sock_b.send(message))
                else:
                    await gather(
                        send(sock_a, coord=buffer[1]), send(sock_b, coord=buffer[0])
                    )
                    buffer = None
            elif "announce_shot" in a_action and "expect_shot" in b_action:
                await gather(
                    send(sock_b, coord=a_action["announce_shot"]), send(sock_a)
                )
            elif "expect_shot" in a_action and "announce_shot" in b_action:
                await gather(
                    send(sock_a, coord=a_action["announce_shot"]), send(sock_b)
                )
            else:
                buffer = a_action["announce_shot"], b_action["announce_shot"]
                await gather(send(sock_a), send(sock_b))

    async def handle_end(
        self, a_payload: "dict[str, Any]", b_payload: "dict[str, Any]"
    ) -> None:
        if "winner" not in a_payload and "winner" not in b_payload:
            return
        # if any player forfeits or yields to the opponent, accept this directly...
        for payload, opponent in zip((a_payload, b_payload), self.clients[::-1]):
            if payload.get("forfeit") or payload.get("winner") == opponent.identifier:
                exc = GameEnd(winner=opponent.identifier)
                break
        # => players do not agree on who won or no one won
        else:
            exc = GameEnd(winner=None)
        message = pack(error=exc)
        await gather(
            self.clients[0].websocket.send(message),
            self.clients[1].websocket.send(message),
        )
        raise exc


class Server:
    def __init__(self) -> None:
        # an unmatched client waiting for a game to start
        self.wait_start: "Tuple[Client, Future[Game]] | None" = None

    async def handle_game(self, websocket: WebSocketServerProtocol) -> None:
        logger.debug("handle connection %s", websocket)
        game = await self.create_game(websocket)
        await game.task

    async def create_game(self, websocket: WebSocketServerProtocol) -> Game:
        # wait for the client to start the game
        identifier, version = await recv(websocket, "identifier", "version")
        logger.info("start %r", identifier)
        # TODO: check version
        # wait for a peer to arrive ...
        if self.wait_start is None:
            self.wait_start = (Client(identifier, websocket), Future())
            game = await self.wait_start[1]
        # ... or connect with a waiting peer
        else:
            peer, this = self.wait_start[0], Client(identifier, websocket)
            if random.random() > 0.5:
                peer, this = this, peer
            game = Game(peer, this)
            self.wait_start[1].set_result(game)
            self.wait_start = None
        return game


async def serve(port: int, hosts: "Sequence[str] | None") -> None:
    server = Server()
    async with websockets.serve(server.handle_game, hosts, port):  # type: ignore[attr-defined]
        logger.info("listening on %s of %s", port, hosts)
        await Future()


if __name__ == "__main__":
    CLI = argparse.ArgumentParser()
    CLI.add_argument("PORT", type=int, help="port to bind to")
    CLI.add_argument(
        "ADDRESS",
        type=str,
        nargs="*",
        help="addresses/hostnames to bind to [default: all]",
    )
    CLI.add_argument("--log-level", help="level of log output", default="WARNING")
    args = CLI.parse_args()
    logging.basicConfig()
    logger.setLevel(args.log_level)
    run_asyncio(serve(args.PORT, args.ADDRESS))
