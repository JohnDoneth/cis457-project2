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
        super(ConnectionDialog, self).__init__(parent)
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

import wx.grid

def create_grid(parent):
    # Create a wxGrid object
    grid = wx.grid.Grid(parent, -1)

    # Then we call CreateGrid to set the dimensions of the grid
    # (100 rows and 10 columns in this example)
    grid.CreateGrid(3, 3)

    # We can set the sizes of individual rows and columns
    # in pixels
    #grid.SetRowSize(0, 60)
    #grid.SetColSize(0, 120)

    # And set grid cell contents as strings
    grid.SetCellValue(0, 0, 'wxGrid is good')

    # We can specify that some cells are read.only
    #grid.SetCellValue(0, 3, 'This is read.only')
    #grid.SetReadOnly(0, 3)

    # Colours can be specified for grid cell contents
    #grid.SetCellValue(3, 3, 'green on grey')
    #grid.SetCellTextColour(3, 3, wx.GREEN)
    #grid.SetCellBackgroundColour(3, 3, wx.LIGHT_GREY)

    # We can specify the some cells will store numeric
    # values rather than strings. Here we set grid column 5
    # to hold floating point values displayed with width of 6
    # and precision of 2
    #grid.SetColFormatFloat(5, 6, 2)
    #grid.SetCellValue(0, 6, '3.1415')

    return grid


class TestFrame(wx.Frame):

    panel = None

    server_connection = None
    connect_button = None
    disconnect_button = None
    search_input = None
    search_button = None

    ftp_input = None
    ftp_button = None

    def __init__(self, parent=None):
        super(TestFrame, self).__init__(parent)
        self.SetTitle("GV NAP")

        # Body sizer
        self.panel = wx.Panel(self, -1)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.connect_button = wx.Button(self.panel, label="Connect")

        self.disconnect_button = wx.Button(self.panel, label="Disconnect")

        self.edit = wx.StaticText(self.panel, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE)
        self.edit_timer = wx.StaticText(
            self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
        )
        vbox.Add(self.connect_button, 1, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.disconnect_button, 1, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.ALL, border=10)

        # Search
        self.search_input = wx.TextCtrl(self.panel, style=wx.TE_LEFT | wx.TE_PROCESS_ENTER, value="")
        self.search_button = wx.Button(self.panel, label="Search")

        AsyncBind(wx.EVT_TEXT_ENTER, self.send_search_request, self.search_input)
        AsyncBind(wx.EVT_BUTTON, self.send_search_request, self.search_button)
        

        H1 = wx.BoxSizer(wx.HORIZONTAL)
        #H1.Add(wx.StaticText(self, label="Search: ", style=wx.ALIGN_CENTER), 2, wx.EXPAND | wx.ALL, border=10)
        H1.Add(self.search_input, 1, wx.EXPAND | wx.ALL, border=10)
        H1.Add(self.search_button, 1, wx.EXPAND | wx.ALL, border=10)
        
        vbox.Add(H1, 1, wx.EXPAND | wx.ALL)
        vbox.Add(create_grid(self.panel), 2, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.ALL, border=10)

        # FTP 
        self.ftp_input = wx.TextCtrl(self.panel, style=wx.TE_LEFT | wx.TE_PROCESS_ENTER, value="")
        self.ftp_button = wx.Button(self.panel, label="Submit Command")

        AsyncBind(wx.EVT_TEXT_ENTER, self.send_ftp_request, self.ftp_input)
        AsyncBind(wx.EVT_BUTTON, self.send_ftp_request, self.ftp_button)
        

        H2 = wx.BoxSizer(wx.HORIZONTAL)
        #H1.Add(wx.StaticText(self, label="Search: ", style=wx.ALIGN_CENTER), 2, wx.EXPAND | wx.ALL, border=10)
        H2.Add(self.ftp_input, 2, wx.EXPAND | wx.ALL, border=10)
        H2.Add(self.ftp_button, 2, wx.EXPAND | wx.ALL, border=10)
        
        vbox.Add(H2, 1, wx.EXPAND | wx.ALL)


        

        # Lay it all out
        self.panel.SetSizer(vbox)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizerAndFit(sizer)
        self.Show()

        self.CenterOnScreen()

        self.update_button()
        StartCoroutine(self.run_file_server_in_background, self)

        AsyncBind(wx.EVT_BUTTON, self.connect, self.connect_button)
        AsyncBind(wx.EVT_BUTTON, self.disconnect, self.disconnect_button)

    async def send_search_request(self, event):
        query = self.search_input.GetValue()
        print(f"sending search request, {query}")

    async def send_ftp_request(self, event):
        query = self.ftp_input.GetValue()
        print(f"sending ftp request, {query}")

    def update_button(self):
        if self.server_connection == None:
            self.connect_button.Enable()
            self.disconnect_button.Disable()
        else:
            self.connect_button.Disable()
            self.disconnect_button.Enable()
            

    async def disconnect(self, event=None):
        print("disconnecting")
        (_, writer) = self.server_connection
        writer.close()
        await writer.wait_closed()
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

        try:
            reader, writer = await connect(
                values.get("address"), values.get("port"), local_port=args.port
            )
            print("connected successfully")

            self.server_connection = (reader, writer)
            self.update_button()
        except Exception:
            print("Failed to connect")


if __name__ == "__main__":
    args = parse_args()

    app = WxAsyncApp()
    frame = TestFrame()
    frame.Show()
    frame.Bind(wx.EVT_CLOSE, lambda event: app.ExitMainLoop())
    app.SetTopWindow(frame)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
