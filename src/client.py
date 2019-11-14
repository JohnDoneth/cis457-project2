#!/bin/python

import wx
import common
import asyncio
import argparse
import os
import base64
import time

from common import ConnectionSpeed, Event
from asyncio import StreamReader, StreamWriter
from typing import Dict
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine
from asyncio.events import get_event_loop


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


class TestFrame(wx.Frame):
    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        button1 = wx.Button(self, label="Submit")
        self.edit = wx.StaticText(
            self, style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE
        )
        self.edit_timer = wx.StaticText(
            self, style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE
        )
        vbox.Add(button1, 2, wx.EXPAND | wx.ALL)
        vbox.AddStretchSpacer(1)
        vbox.Add(self.edit, 1, wx.EXPAND | wx.ALL)
        vbox.Add(self.edit_timer, 1, wx.EXPAND | wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        AsyncBind(wx.EVT_BUTTON, self.async_callback, button1)
        StartCoroutine(self.update_clock, self)

    async def async_callback(self, event):
        self.edit.SetLabel("Button clicked")
        await asyncio.sleep(1)
        self.edit.SetLabel("Working")
        await asyncio.sleep(1)
        self.edit.SetLabel("Completed")

    async def update_clock(self):
        while True:
            self.edit_timer.SetLabel(time.strftime("%H:%M:%S"))
            await asyncio.sleep(0.5)

    async def run_file_server_in_background(self):
        server_task = asyncio.create_task(spawn_file_server(1234))

    async def connect_to_server(self):
        reader, writer = await connect("127.0.0.1", 12345, local_port=args.port)


if __name__ == "__main__":
    args = parse_args()

    app = WxAsyncApp()
    frame = TestFrame()
    frame.Show()
    app.SetTopWindow(frame)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
