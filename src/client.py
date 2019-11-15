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
from wxasync import AsyncBind, WxAsyncApp, StartCoroutine, AsyncShowDialog
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


class ConnectionDialog(wx.Dialog):

    server_address = None
    server_port = None
    connection_speed = None

    def IsModal(self):
        return True

    def get_values(self):
        return dict(
            address=self.server_address.GetValue(),
            port=self.server_port.GetValue()
            # connection_speed=dial
        )

    def __init__(self, parent=None):
        super(ConnectionDialog, self).__init__(parent, style=wx.RESIZE_BORDER)
        self.SetTitle("Connect")

        textMarginTop = wx.SizerFlags(0).Border(wx.TOP | wx.RIGHT, 2)

        flagsExpand = wx.SizerFlags(1)
        flagsExpand.Expand()
        flagsExpand.Align(wx.ALIGN_CENTER)

        self.server_address = wx.TextCtrl(self, style=wx.TE_LEFT, value="127.0.0.1")
        self.server_port = wx.TextCtrl(self, style=wx.TE_LEFT, value="1234")

        # self.connection_speed = wx.ComboBox()

        box_sizer = wx.BoxSizer(orient=wx.VERTICAL)
        flex_sizer = wx.FlexGridSizer(2, 4, 4)
        flex_sizer.AddGrowableCol(1)

        # Server Address
        flex_sizer.Add(
            wx.StaticText(
                self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, label="Server Address"
            ),
            textMarginTop,
        )
        flex_sizer.Add(self.server_address, flagsExpand)

        # Server Port
        flex_sizer.Add(
            wx.StaticText(
                self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE, label="Server Port"
            ),
            textMarginTop,
        )
        flex_sizer.Add(self.server_port, flagsExpand)

        # Connection Speed
        # flex_sizer.Add(wx.StaticText(self, label="Connection Speed"))
        # flex_sizer.Add(self.connection_speed, flag=wx.EXPAND | wx.HORIZONTAL)

        box_sizer.Add(flex_sizer, wx.SizerFlags(1).Expand().Border(wx.ALL, 10))
        box_sizer.Add(
            self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL),
            flag=wx.ALIGN_BOTTOM | wx.BOTTOM | wx.EXPAND,
            border=10,
        )
        self.SetSizer(box_sizer)
        # self.SetSizeWH(400, 200)


class TestFrame(wx.Frame):

    server_connection = None

    connect_button = None

    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.connect_button = wx.Button(self, label="Connect")
        self.edit = wx.StaticText(self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
        self.edit_timer = wx.StaticText(
            self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
        )
        vbox.Add(self.connect_button, 2, wx.EXPAND | wx.ALL, border=10)
        vbox.AddStretchSpacer(1)
        vbox.Add(self.edit, 1, wx.EXPAND | wx.ALL)
        vbox.Add(self.edit_timer, 1, wx.EXPAND | wx.ALL)
        self.SetSizer(vbox)
        self.Layout()
        self.CenterOnScreen()

        self.update_button()
        # StartCoroutine(self.update_clock, self)
        # StartCoroutine(self.run_file_server_in_background, self)

    def update_button(self):
        # self.Unbind(wx.EVT_BUTTON)

        print(self.connect_button.Unbind(wx.EVT_BUTTON))

        if self.server_connection == None:
            self.connect_button.SetLabel("Connect")
            AsyncBind(wx.EVT_BUTTON, self.connect, self.connect_button)
        else:
            self.connect_button.SetLabel("Disconnect")
            AsyncBind(wx.EVT_BUTTON, self.disconnect, self.connect_button)

    async def disconnect(self, event=None):
        print("disconnecting")
        self.server_connection = None
        self.update_button()
        pass

    async def connect(self, event=None):
        self.Disable()

        dialog = ConnectionDialog()
        result = await AsyncShowDialog(dialog)

        if result == wx.ID_OK:
            print("was ok")

            values = dialog.get_values()
            print(values)

            await self.connect_to_server(values)

            dialog.Destroy()

        self.Enable()
        self.Raise()

    # async def update_clock(self):
    #    while True:
    #        self.edit_timer.SetLabel(time.strftime("%H:%M:%S"))
    #        await asyncio.sleep(0.5)

    async def run_file_server_in_background(self):
        server_task = asyncio.create_task(spawn_file_server(1234))

    async def connect_to_server(self, values):
        reader, writer = await connect(
            values.get("address"), values.get("port"), local_port=args.port
        )
        print("connected successfully")

        self.server_connection = (reader, writer)
        self.update_button()


if __name__ == "__main__":
    args = parse_args()

    app = WxAsyncApp()
    frame = TestFrame()
    frame.Show()
    frame.Bind(wx.EVT_CLOSE, lambda event: app.ExitMainLoop())
    app.SetTopWindow(frame)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
