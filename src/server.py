#!/bin/python

# import socket programming library
import base64
import json
import os
import socket
import struct
import threading
import common
import asyncio


def filter_files(path):
    _, extension = os.path.splitext(path[0])

    if extension == ".py":
        return False
    else:
        return True


def handle_request(method: str, request):

    if method == "CONNECT":
        username = request["username"]
        hostname = request["hostname"]
        speed = request["speed"]
        files = request["files"]

    else:
        # invalid method
        pass


# thread function
def threaded(client):
    while True:

        request = common.recv_json(client)

        if request is None:
            print("a client has disconnected")
            break

        print("-> Received Request:")
        print(json.dumps(request, indent=4, sort_keys=True))

        if not request["method"]:
            print("Invalid Request: missing method field.")
            continue

        handle_request(request["method"].upper(), request)

    client.close()


async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info("peername")

    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, "127.0.0.1", 12345)

    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        pass
