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

from ftp.ftp_client import FTPClient
from common import Event
from asyncio import StreamReader, StreamWriter

from typing import Dict

VALID_METHODS = ["CONNECT", "LIST"]


class Client:
    username: str = ""
    hostname: str = ""
    speed: str = ""
    files: {} = {}

    def __init__(self, username: str, hostname: str, speed: str, files: Dict):
        self.username = username
        self.hostname = hostname
        self.speed = speed
        self.files = files


class Server:

    clients: [] = []
    files: [] = []

    def __init__(self):
        pass

    def run(self):
        asyncio.run(self.serve())

    async def handle_request(
        self, method: str, request, client, reader: StreamReader, writer: StreamWriter
    ) -> Client:

        if method == "CONNECT":
            username = request["username"]
            hostname = request["hostname"]
            speed = request["speed"]
            files = request["files"]

            print(f"Accepted new client with hostname: {hostname}")
            client = Client(username, hostname, speed, files)
            self.clients.append(client)
            await common.send_json(writer, {"success": "connection successful"})
            return client

        elif method == "LIST":
            files = []

            for c in self.clients:
                if c.username != client.username:
                    for file in c.files:
                        files.append(
                            {
                                "filename": file["filename"],
                                "hostname": c.hostname,
                                "speed": c.speed,
                            }
                        )

            print(files)

            await common.send_json(writer, files)

        elif method == "KEYWORD":
            keyword = request["keyword"]

            files_to_search = []

            for c in self.clients:
                if c.username != client.username:
                    for file in c.files:
                        files_to_search.append(
                            {
                                "filename": file["filename"],
                                "hostname": c.hostname,
                                "speed": c.speed,
                            }
                        )

            files = []

            # get each file
            for file in files_to_search:
                hostname = file["hostname"]
                address, port = hostname.split(":")

                ftpclient = FTPClient()

                await ftpclient.connect(address, port)
                contents = await ftpclient.retrieve_string(file["filename"])
                if keyword in contents:
                    files.append(file)

            await common.send_json(writer, files)

        else:
            # invalid method
            await common.send_json(
                writer,
                {
                    "error": f"invalid method '{method}', expected one of {VALID_METHODS}"
                },
            )

    async def serve(self):
        server = await asyncio.start_server(self.handle_connect, "127.0.0.1", 12345)

        addr = server.sockets[0].getsockname()
        print(f"Serving on {addr}")

        async with server:
            await server.serve_forever()

    async def handle_connect(self, reader: StreamReader, writer: StreamWriter):

        client = None

        while True:
            request = await common.recv_json(reader)

            if request is None:
                print(f"Client has disconnected: {client.hostname}")
                self.clients.remove(client)
                break

            if client is None:
                print("-> Received Request:")
            else:
                print(f"-> Received Request from {client.hostname}:")

            print(json.dumps(request, indent=4, sort_keys=False))

            if not request["method"]:
                print("Invalid Request: missing method field.")
                await common.send_json(
                    writer, {"error": "invalid request: missing method field"}
                )
            else:
                etc = await self.handle_request(
                    request["method"], request, client, reader, writer
                )

                if etc is not None:
                    client = etc


def filter_files(path):
    _, extension = os.path.splitext(path[0])

    if extension == ".py":
        return False
    else:
        return True


if __name__ == "__main__":

    try:
        Server().run()
    except KeyboardInterrupt:
        print()
        pass
