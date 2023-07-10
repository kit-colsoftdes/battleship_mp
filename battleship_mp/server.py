from typing import NamedTuple, Tuple, Iterable, Any, Sequence
from asyncio import gather, Future, ensure_future, run as run_asyncio
import argparse
import random

import websockets
from websockets.server import WebSocketServerProtocol

from .messages import pack, unpack, unpack_keys
from .exceptions import Deadlock, GameEnd


def send(_ws: WebSocketServerProtocol, **payload):
    return _ws.send(pack(payload))


async def recv(_ws: WebSocketServerProtocol, *keys: str) -> Iterable[Any]:
    return unpack_keys(await _ws.recv(), keys)


class Client(NamedTuple):
    """A client waiting for matching game"""

    identifier: str
    websocket: WebSocketServerProtocol


class Game:
    def __init__(self, client_a: Client, client_b: Client):
        self.clients = client_a, client_b
        self.task = ensure_future(self.run())

    async def run(self):
        await self.handle_start()
        await self.handle_placement()

    async def handle_start(self):
        for idx, client in enumerate(self.clients):
            await send(
                client.websocket,
                identifier=self.clients[(idx + 1) % 2].identifier,
                first=(idx == 0),
            )

    async def handle_placement(self):
        keys = "sizes", "coords", "vertical"
        ships = await gather(
            recv(self.clients[0].websocket, *keys),
            recv(self.clients[1].websocket, *keys),
        )
        await gather(
            send(self.clients[0].websocket, **ships[1]),
            send(self.clients[1].websocket, **ships[0]),
        )

    async def handle_shots(self):
        sock_a, sock_b = self.clients[0].websocket, self.clients[1].websocket
        buffer: "tuple[Any, Any]| None" = None
        while True:
            a_action, b_action = map(unpack, await gather(sock_a.recv(), sock_b.recv()))
            await self.handle_end(a_action, b_action)
            if "expect_shot" in a_action and "expect_shot" in b_action:
                if buffer is None:
                    message = pack(error=Deadlock("both peers wait for shot"))
                    await gather(sock_a.send(message), sock_b.send(message))
                else:
                    await gather(
                        send(sock_a, coord=buffer[0]), send(sock_b, coord=buffer[1])
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

    async def handle_end(self, a_payload, b_payload):
        if "winner" not in a_payload and "winner" not in b_payload:
            return
        # if any player forfeits or yields to the opponent, accept this directly...
        for payload, client, opponent in zip(
            (a_payload, b_payload), self.clients, self.clients[::-1]
        ):
            if payload.get("forfeit") or payload.get("winner") == opponent.identifier:
                message = pack(error=GameEnd(winner=opponent.identifier))
                await gather(
                    client.websocket.send(message), opponent.websocket.send(message)
                )
        # => players do not agree on who won or no one won
        message = pack(error=GameEnd(winner=None))
        await gather(
            self.clients[0].websocket.send(message),
            self.clients[1].websocket.send(message),
        )


class Server:
    def __init__(self):
        # an unmatched client waiting for a game to start
        self.wait_start: "Tuple[Client, asyncio.Future[Game]] | None" = None

    async def handle_game(self, websocket: WebSocketServerProtocol):
        game = await self.create_game(websocket)
        await game.task

    async def create_game(self, websocket: WebSocketServerProtocol):
        # wait for the client to start the game
        identifier, version = await recv(websocket, "identifier", "version")
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


async def serve(port: int, hosts: "Sequence[str, ...] | None"):
    server = Server()
    async with websockets.serve(server.handle_game, hosts, port):
        await Future()


if __name__ == "__main__":
    CLI = argparse.ArgumentParser()
    CLI.add_argument("PORT", type=int, help="port to bind to")
    CLI.add_argument(
        "ADDRESS",
        type=str,
        nargs="*",
        help="addresses/hostnames to bind to [default: all]"
    )
    args = CLI.parse_args()
    run_asyncio(serve(args.port, args.hosts))