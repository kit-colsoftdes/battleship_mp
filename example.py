"""
Test script to simulate a multiplayer game including a server and two "AI" clients

For simplicity, the game is run on a 3x3 board with just two ships per player.
All "AI" decisions are random:
each player randomly chooses ship positions via :py:func:`create_positions`
and randomly goes through all possible :py:data:`SHOTS`.

Two representations are used for the board:
compressed as a sequence of :py:data:`~.client.SHIP_PLACEMENT`
and expanded as a board represented by rows of fields.
The former can be converted to the latter by :py:func:`expand`,
and the board is most suitable to compute the game state.
For convenience, :py:func:`defeated` can check if a board
indicates that its player has lost.

A fully working client for an "AI" player is implemented by :py:func:`play`.
It goes through all steps of using the API to run a game:
- connecting to the server,
- starting a multiplayer game,
- setting ships on the board, and
- exchanging shots until one player wins.

The example is driven by :py:func:`simulate`, which is rather complex
as it needs to handle both the server and the two clients in :py:mod:`asyncio`.
It is not educational, other than perhaps for setting ``os.environ[SERVER_URL_ENV]``.
"""
import os
import asyncio
import random
import string
import sys
import logging

from battleship_mp import client, server, SERVER_URL_ENV


SHOTS = tuple((y, x) for y in range(3) for x in range(3))


def create_positions() -> "tuple[client.SHIP_PLACEMENT, client.SHIP_PLACEMENT]":
    """Randomly place a 3 and 1 ship on a 3x3 board"""
    vertical3 = not random.getrandbits(1)
    offset3 = random.getrandbits(1) * 2
    offset1 = random.randint(0, 2)
    return (
        (3, (0, offset3) if vertical3 else (offset3, 0), vertical3),
        (1, (offset1, 2 - offset3) if vertical3 else (2 - offset3, offset1), vertical3),
    )


def expand(*placements: client.SHIP_PLACEMENT) -> "list[list[str]]":
    """Expand ship placements to a 3x3 board; ships are represented by numbers"""
    board = [[" ", " ", " "] for _ in range(3)]
    for length, (y, x), vertical in placements:
        if vertical:
            for offset in range(length):
                board[y + offset][x] = str(length)
        else:
            for offset in range(length):
                board[y][x + offset] = str(length)
    return board


def defeated(board: "list[list[str]]") -> bool:
    """Check if all ships on the board are defeated"""
    return not any(field.isdigit() for row in board for field in row)


def draw(*boards: "list[list[str]]"):
    """Print one or several boards"""
    print("\n".join("   ".join("".join(row) for row in rows) for rows in zip(*boards)))


def play(name: str):
    """Single client playing a game using simultaneous shooting"""
    with client.GameSession.connect(name) as session:
        # start the game
        enemy = session.opponent
        print(f"{name} vs {enemy}")
        # exchange positions and prepare boards
        my_positions = create_positions()
        enemy_positions = session.place_ships(*my_positions)
        my_board = expand(*my_positions)
        enemy_board = expand(*enemy_positions)
        # exchange shots
        for my_shot in random.sample(SHOTS, len(SHOTS)):
            session.announce_shot(my_shot)
            enemy_shot = session.expect_shot()
            for (y, x), board in ((my_shot, enemy_board), (enemy_shot, my_board)):
                board[y][x] = "X"
            # check if the game is done, i.e. if any player won
            defeat = defeated(my_board), defeated(enemy_board)
            if defeat == (False, False):
                continue
            elif defeat == (True, True):
                winner = None
                session.end_game(None)
            elif defeat == (True, False):
                winner = enemy
                session.end_game(enemy)
            elif defeat == (False, True):
                winner = name
                session.end_game(name)
            break
        else:
            raise RuntimeError("Placing all shots should have ended the game...")
        print(f"{name} vs {enemy} => {winner}")


PLAYERS = string.ascii_letters + string.digits + "@$%&?"


async def simulate():
    """Run a full game, including server and two clients"""
    host, port = "localhost", 8765  # chosen by fair roll of dice
    os.environ[SERVER_URL_ENV] = f"ws://{host}:{port}"
    server_task = asyncio.ensure_future(server.serve(port, [host]))
    await asyncio.sleep(0.01)
    for _ in range(64):
        players = random.sample(PLAYERS, 2)
        print("###", players[0], "vs", players[1], "###")
        await asyncio.gather(*(asyncio.to_thread(play, player) for player in players))
        await asyncio.sleep(0.5)
    server_task.cancel()


if __name__ == "__main__":
    if "debug" in sys.argv:
        logging.getLogger("battleship_mp").setLevel("DEBUG")
    asyncio.run(simulate())
