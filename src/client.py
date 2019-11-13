#!/bin/python

from client.gui import ClientGUI

import common
import asyncio
import argparse
import os
import base64

from common import ConnectionSpeed, Event
from asyncio import StreamReader, StreamWriter
from typing import Dict


async def handle_incoming(reader: StreamReader, writer: StreamWriter):
    request = await common.recv_json(reader)

    handle_request(request, reader, writer)


async def handle_request(request: Dict, reader: StreamReader, writer: StreamWriter):
    print(request)

    if request["method"].upper().startswith("RETRIEVE"):
        handle_file_request(request, reader, writer)

    pass


async def handle_file_request(
    request: Dict, reader: StreamReader, writer: StreamWriter
):

    filename = request["filename"]

    if not os.path.exists(filename):
        common.send_json(writer, {"error": "file does not exist"})
        return

    with open(filename, "rb") as infile:
        contents = infile.read()

        # base64 encode the binary file
        contents = base64.b64encode(contents).decode("utf-8")

        common.send_json(writer, {"filename": filename, "content": contents})


async def spawn_file_server(local_port):
    server = await asyncio.start_server(handle_incoming, "127.0.0.1", local_port)
    addr = server.sockets[0].getsockname()

    print("Server started")
    print(f"Waiting for file requests on {addr}")

    async with server:
        await server.serve_forever()


async def connect(remote_host, remote_port, local_port):
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", 12345)
        return reader, writer
    except ConnectionRefusedError:
        print(
            f"Failed to connect to {remote_host}:{remote_port}. Please ensure the remote IP address & port are valid and that the host is online."
        )
        raise ConnectionRefusedError

    await common.send_json(
        writer,
        {
            "method": "CONNECT",
            "username": "john",
            "hostname": "127.0.0.1",
            "port": local_port,
            "speed": ConnectionSpeed.DIAL_UP,
            "files": [{"filename": "meme.png"}],
        },
    )

    response = await common.recv_json(reader)

    error = response.get("error")
    if error is not None:
        print(f"An error ocurred: {error}")
        return
    else:
        print("Connected to remote server")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", metavar="PORT", type=int, help="port to serve files on", default=1234,
    )
    return parser.parse_args()


async def main(pipe):
    args = parse_args()

    server_task = asyncio.create_task(spawn_file_server(args.port))

    reader, writer = await connect("127.0.0.1", 12345, local_port=args.port)

    # gui = ClientGUI()

    # asyncio.get_running_loop().run_forever()

    while True:
        if pipe.poll():
            event = pipe.recv()
            print(event)

            if event == Event.QUIT:
                break
        else:
            await asyncio.sleep(0.1)


from multiprocessing import Process, Pipe


def f(conn):
    # conn.send([42, None, 'hello'])
    # conn.close()
    client = ClientGUI(conn)


if __name__ == "__main__":

    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()
    # print(parent_conn.recv())  # prints "[42, None, 'hello']"
    # p.join()

    # asyncio.get_event_loop().run_forever()
    asyncio.run(main(parent_conn))

    # client = ClientGUI()
