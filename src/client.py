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


async def connect(remote_host, remote_port, username, hostname, connection_speed, local_port):
    
    reader, writer = await asyncio.open_connection("127.0.0.1", 12345)
    
    #except ConnectionRefusedError:
    #    print(
    #        f"Failed to connect to {remote_host}:{remote_port}. Please ensure the remote IP address & port are valid and that the host is online."
    #    )
    #    raise ConnectionRefusedError

    await common.send_json(
        writer,
        {
            "method": "CONNECT",
            "username": username,
            "hostname": hostname,
            "port": local_port,
            "speed": connection_speed,
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

    return reader, writer


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


def create_list(parent):
    # Create a wxGrid object
    listctrl = wx.ListCtrl(parent, -1)

    listctrl.AppendColumn("Filename")
    listctrl.AppendColumn("Hostname")

    return listctrl


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

        self.edit = wx.StaticText(
            self.panel, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
        )
        self.edit_timer = wx.StaticText(
            self, style=wx.ALIGN_RIGHT | wx.ST_NO_AUTORESIZE
        )
        vbox.Add(self.connect_button, 1, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(self.disconnect_button, 1, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.ALL, border=10)

        # Search
        self.search_input = wx.TextCtrl(
            self.panel, style=wx.TE_LEFT | wx.TE_PROCESS_ENTER, value=""
        )
        self.search_button = wx.Button(self.panel, label="Search")

        AsyncBind(wx.EVT_TEXT_ENTER, self.send_search_request, self.search_input)
        AsyncBind(wx.EVT_BUTTON, self.send_search_request, self.search_button)

        H1 = wx.BoxSizer(wx.HORIZONTAL)
        H1.Add(
            wx.StaticText(
                self.panel, label="Search: ", style=wx.ST_NO_AUTORESIZE | wx.ALIGN_RIGHT
            ),
            0,
            wx.ALL | wx.ALIGN_CENTER_VERTICAL,
            border=10,
        )
        H1.Add(self.search_input, 1, wx.EXPAND | wx.ALL, border=10)
        H1.Add(self.search_button, 0, wx.EXPAND | wx.ALL, border=10)

        vbox.Add(H1, 1, wx.EXPAND | wx.ALL)
        vbox.Add(create_list(self.panel), 2, wx.EXPAND | wx.ALL, border=10)
        vbox.Add(wx.StaticLine(self.panel), 0, wx.EXPAND | wx.ALL, border=10)

        # FTP

        ftp_sbox = wx.StaticBox(self.panel, -1, "FTP")
        ftp_sboxsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.ftp_input = wx.TextCtrl(
            ftp_sbox, style=wx.TE_LEFT | wx.TE_PROCESS_ENTER, value=""
        )
        self.ftp_button = wx.Button(ftp_sbox, label="Submit Command")

        AsyncBind(wx.EVT_TEXT_ENTER, self.send_ftp_request, self.ftp_input)
        AsyncBind(wx.EVT_BUTTON, self.send_ftp_request, self.ftp_button)

        # H2.Add(wx.StaticText(self.panel, label="Search: "), 2, wx.EXPAND | wx.ALL, border=10)
        ftp_sboxsizer.Add(self.ftp_input, 1, wx.EXPAND | wx.ALL | wx.CENTER, border=5)
        ftp_sboxsizer.Add(self.ftp_button, 0, wx.EXPAND | wx.ALL | wx.CENTER, border=5)

        ftp_sbox.SetSizer(ftp_sboxsizer)
        vbox.Add(ftp_sbox, 1, wx.EXPAND | wx.ALL | wx.CENTER, border=15)

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


from client.gui import MyFrame


class ErrorDialog(wx.Dialog):

    message = ""

    def __init__(self, message):
        # begin wxGlade: ErrorDialog.__init__

        wx.Dialog.__init__(self, None, style=wx.DEFAULT_DIALOG_STYLE)
        self.SetTitle("Error")

        self.message = message

        self.__do_layout()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ErrorDialog.__do_layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        label_8 = wx.StaticText(self, wx.ID_ANY, self.message)
        sizer.Add(label_8, 0, wx.ALIGN_CENTER | wx.ALL, 20)

       

        sizer.Add(self.CreateButtonSizer(flags=wx.OK), 0, wx.ALIGN_RIGHT | wx.ALL, 20)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()
        # end wxGlade
        



class MyApp(WxAsyncApp):

    server_connection = None

    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        self.frame.Bind(wx.EVT_CLOSE, lambda event: app.ExitMainLoop())

        StartCoroutine(self.run_file_server_in_background, self)

        AsyncBind(wx.EVT_BUTTON, self.OnConnect, self.frame.connect_button)
        AsyncBind(wx.EVT_BUTTON, self.OnDisconnect, self.frame.disconnect_button)

        AsyncBind(wx.EVT_BUTTON, self.GetAndDisplayFiles, self.frame.search_button)

        self.update_gui()

        return True


    def update_gui(self):

        connected = self.server_connection is not None

        if_connected = [
            (self.frame.connect_button, False),
            (self.frame.disconnect_button, True),
            (self.frame.search_input, True),
            (self.frame.search_button, True),
            (self.frame.ftp_input, True),
            (self.frame.ftp_button, True),

            # connection stuff
            (self.frame.server_hostname, False),
            (self.frame.server_port, False),
            (self.frame.username, False),
            (self.frame.hostname, False),
            (self.frame.connection_speed, False),
        ]

        if connected:
            for (widget, state) in if_connected:
                if state:
                    widget.Enable()
                else:
                    widget.Disable()

        else:
            for (widget, state) in if_connected:
                if state:
                    widget.Disable()
                else:
                    widget.Enable()


    async def run_file_server_in_background(self):
        server_task = asyncio.create_task(spawn_file_server(1234))


    async def OnDisconnect(self, event):
        print("disconnecting")
        try:
            (_, writer) = self.server_connection
            writer.close()
            await writer.wait_closed()
        except ConnectionResetError:
            pass
        self.server_connection = None
        self.update_gui()
        

    async def OnConnect(self, event):

        self.frame.connect_button.Disable()

        server_hostname = self.frame.server_hostname.GetValue()
        server_port = self.frame.server_port.GetValue()
        username = self.frame.username.GetValue()
        hostname = self.frame.hostname.GetValue()
        connection_speed = self.frame.connection_speed.GetValue()

        print(server_hostname, server_port, username, hostname, connection_speed)

        try:
            reader, writer = await connect(
                server_hostname, server_port, username, hostname, connection_speed, local_port=1234
            )
            print("connected successfully")

            self.server_connection = (reader, writer)
            #self.update_button()
        except Exception:
            print("Failed to connect")

            dlg = ErrorDialog("Failed to connect, is the host online?")
            await AsyncShowDialog(dlg)

        self.update_gui()
        await self.GetAndDisplayFiles(None)

    
    async def GetAndDisplayFiles(self, event):

        # Get the files
        (reader, writer) = self.server_connection

        await common.send_json(writer, {
            "method": "LIST",
        })

        response = await common.recv_json(reader)

        # Update the ListCtrl
        listctrl = self.frame.search_output
        listctrl.DeleteAllItems()

        for file in response:
            filename = file["filename"]
            hostname = file["hostname"]
            speed = file["speed"]

            listctrl.Append([filename, hostname, speed])


if __name__ == "__main__":
    args = parse_args()

    app = MyApp(0)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
