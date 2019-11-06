#!/bin/python

from client.gui import ClientGUI

import common
import asyncio

from asyncio import StreamReader, StreamWriter
from typing import Dict


async def handle_incomming_connection(reader: StreamReader, writer: StreamWriter):
    request = await common.recv_json(reader)

    handle_request(request, reader, writer)


async def handle_request(request: Dict, reader: StreamReader, writer: StreamWriter):

    if request["method"] == "GET":
        pass

    pass


async def main():

    gui = ClientGUI()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port", metavar="PORT", type=int, help="port to serve files on", default=1234,
    )

    args = parser.parse_args()

    local_port = args.port

    remote_host = "127.0.0.1"
    remote_port = 12345

    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", 12345)
    except ConnectionRefusedError:
        print(
            f"Failed to connect to {remote_host}:{remote_port}. Please ensure the remote IP address & port are valid and that the host is online."
        )
        return

    await common.send_json(
        writer,
        {
            "method": "CONNECT",
            "username": "john",
            "hostname": "127.0.0.1",
            "port": local_port,
            "speed": "dial-up",
            "files": [{"filename": "meme.png"}],
        },
    )

    response = await common.recv_json(reader)
    if response.get("error") is not None:
        print("error")
        return

    else:
        print("File descriptions recieved by central server. Starting file server...")

        server = await asyncio.start_server(handle_request, "127.0.0.1", local_port)
        addr = server.sockets[0].getsockname()

        print("Server started")
        print(f"Waiting for file requests on {addr}")

        async with server:
            await server.serve_forever()

        print(response)


if __name__ == "__main__":

    asyncio.run(main())

    # client = ClientGUI()
