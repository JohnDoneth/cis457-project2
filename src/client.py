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

from ftp.ftp_client import FTPClient
from ftp.ftp_server import FTPServer
from client.gui import MyFrame


async def connect(
    remote_host, remote_port, username, hostname, connection_speed, local_port
):

    reader, writer = await asyncio.open_connection(remote_host, remote_port)

    files = []

    for f in os.listdir("."):
        if os.path.isfile(f):
            files.append(dict(filename=f))

    await common.send_json(
        writer,
        {
            "method": "CONNECT",
            "username": username,
            "hostname": hostname,
            "port": local_port,
            "speed": connection_speed,
            "files": files,
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

    ftp_client = None

    args = parse_args()

    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        self.frame.Bind(wx.EVT_CLOSE, lambda event: app.ExitMainLoop())

        self.frame.hostname.SetValue(f"127.0.0.1:{args.port}")

        self.ftp_client = FTPClient(self.frame.ftp_output)

        StartCoroutine(self.run_file_server_in_background, self)

        AsyncBind(wx.EVT_BUTTON, self.OnConnect, self.frame.connect_button)
        AsyncBind(wx.EVT_BUTTON, self.OnDisconnect, self.frame.disconnect_button)

        AsyncBind(wx.EVT_BUTTON, self.GetAndDisplayFiles, self.frame.search_button)
        AsyncBind(wx.EVT_TEXT_ENTER, self.GetAndDisplayFiles, self.frame.search_input)

        AsyncBind(wx.EVT_BUTTON, self.OnFTPCommand, self.frame.ftp_button)
        AsyncBind(wx.EVT_TEXT_ENTER, self.OnFTPCommand, self.frame.ftp_input)

        self.update_gui()

        return True

    def update_gui(self):

        connected = self.server_connection is not None

        if_connected = [
            (self.frame.connect_button, False),
            (self.frame.disconnect_button, True),
            (self.frame.search_input, True),
            (self.frame.search_button, True),
            # (self.frame.ftp_input, True),
            # (self.frame.ftp_button, True),
            # connection stuff
            (self.frame.server_hostname, False),
            (self.frame.server_port, False),
            (self.frame.username, False),
            (self.frame.hostname, False),
            (self.frame.connection_speed, False),
            (self.frame.search_output, True),
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
        server = FTPServer()

        server_task = asyncio.create_task(server.run_forever(args.port))

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

        if server_hostname == "":
            await AsyncShowDialog(ErrorDialog("Please specify the server hostname"))
            self.update_gui()
            return
        if server_port == "":
            await AsyncShowDialog(ErrorDialog("Please specify the server port"))
            self.update_gui()
            return
        if username == "":
            await AsyncShowDialog(ErrorDialog("Please specify a username"))
            self.update_gui()
            return
        if hostname == "":
            await AsyncShowDialog(ErrorDialog("Please specify a hostname"))
            self.update_gui()
            return

        print(server_hostname, server_port, username, hostname, connection_speed)

        try:
            reader, writer = await connect(
                server_hostname,
                server_port,
                username,
                hostname,
                connection_speed,
                local_port=1234,
            )
            print("connected successfully")

            self.server_connection = (reader, writer)

        except Exception:
            dlg = ErrorDialog("Failed to connect, is the host online?")
            await AsyncShowDialog(dlg)

        self.update_gui()
        await self.GetAndDisplayFiles(None)

    async def GetAndDisplayFiles(self, event):
        keyword = self.frame.search_input.GetValue()
        self.frame.search_input.SetValue("")

        # Get the files
        (reader, writer) = self.server_connection

        if keyword == "":
            await common.send_json(writer, {"method": "LIST",})
        else:
            await common.send_json(writer, {"method": "KEYWORD", "keyword": keyword,})

        response = await common.recv_json(reader)

        # Update the ListCtrl
        listctrl = self.frame.search_output
        listctrl.DeleteAllItems()

        for file in response:
            filename = file["filename"]
            hostname = file["hostname"]
            speed = file["speed"]

            listctrl.Append([filename, hostname, speed])

        self.autosize_list_columns()

    def autosize_list_columns(self):
        listctrl = self.frame.search_output

        for col in range(0, listctrl.GetColumnCount()):
            listctrl.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)
            wh = listctrl.GetColumnWidth(col)
            listctrl.SetColumnWidth(col, wx.LIST_AUTOSIZE)
            wc = listctrl.GetColumnWidth(col)
            if wh > wc:
                listctrl.SetColumnWidth(col, wx.LIST_AUTOSIZE_USEHEADER)

    async def OnFTPCommand(self, event):

        cmd = self.frame.ftp_input.GetValue()
        self.frame.ftp_input.SetValue("")

        await self.ftp_client.try_command(cmd)


if __name__ == "__main__":
    args = parse_args()

    app = MyApp(0)

    loop = get_event_loop()
    loop.run_until_complete(app.MainLoop())
