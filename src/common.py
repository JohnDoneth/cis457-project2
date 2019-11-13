import base64
import json
import os
import socket
import struct
import threading

from asyncio import StreamWriter, StreamReader
from asyncio.streams import IncompleteReadError


from enum import Enum


class Event(Enum):
    QUIT = "QUIT"


class ConnectionSpeed(str, Enum):
    DIAL_UP = "dial-up"
    DSL = "dsl"
    GIGABIT = "gigabit"


# https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


async def recv_json(reader: StreamReader):
    """
    Reads a 4 byte length-prefixed JSON message and returns a decoded JSON object.

    If the reader fails to read the message, `None` is returned. 
    """
    try:
        raw_length = await reader.readexactly(4)
        length = struct.unpack(">I", raw_length)[0]

        body = bytes()
        while len(body) != length:
            body += await reader.read(length)

        body = body.decode("utf-8")
        return json.loads(body)
    except IncompleteReadError:
        return None


async def send_json(writer: StreamWriter, body):
    # encode the data as stringified-json
    encoded = json.dumps(body)
    encoded = encoded.encode("utf-8")

    # get the size of the encoded body
    size = struct.pack(">I", len(encoded))

    # write the size
    writer.write(size)

    # write the encoded body
    writer.write(encoded)


async def send_response(writer: StreamWriter, body):
    await send_json(writer, body)

    print("<- Sent Response:")
    print(json.dumps(body, indent=4, sort_keys=True))
    # threaded_print("<- Sent Response:")
    # threaded_print(json.dumps(body, indent=4, sort_keys=True))
