import asyncio
import os
import common
import base64
import wx


class FTPClient:
    reader = None
    writer = None

    output = None

    def __init__(self, output=None):
        self.output = output
        pass

    def info(self, msg):
        if self.output:
            self.output.SetDefaultStyle(wx.TextAttr(wx.BLACK))
            self.output.AppendText(f"{msg}\n")

    def error(self, msg):
        if self.output:
            self.output.SetDefaultStyle(wx.TextAttr(wx.RED))
            self.output.AppendText(f"{msg}\n")

    def success(self, msg):
        if self.output:
            self.output.SetDefaultStyle(wx.TextAttr(wx.Colour(0, 100, 0)))
            self.output.AppendText(f"{msg}\n")

    def column_print(self, columns):
        col_width = max(len(word) for row in columns for word in row) + 2  # padding
        for row in columns:
            self.info("\t" + "".join(word.ljust(col_width) for word in row))

    def require_connection(self):
        self.error(
            "A connection must be established first. Use the CONNECT <IP> <PORT> command."
        )

    async def recv_json(self):
        return await common.recv_json(self.reader)

    async def send_json(self, body):
        return await common.send_json(self.writer, body)

    async def try_command(self, command):

        line = command.rstrip()
        cmd = line.split()

        if len(cmd) == 0:
            return

        self.info(f"> {command}")

        if cmd[0].upper() == "CONNECT":
            if len(cmd) != 3:
                self.error("CONNECT requires 2 parameters: <IP> <PORT>")
            else:
                await self.connect(cmd[1], cmd[2])

        elif cmd[0].upper() == "RETRIEVE":
            if len(cmd) != 2:
                self.error("RETRIEVE requires a single parameter: <FILENAME>")
            else:
                await self.retrieve(cmd[1])

        # Do not support remote editing of others contents
        #
        # elif cmd[0].upper() == "STORE":
        #    if len(cmd) != 2:
        #        self.error("STORE requires a single parameter: <FILENAME>")
        #    else:
        #        await self.send_file(cmd[1])

        # elif cmd[0].upper() == "DELETE":
        #    if len(cmd) != 2:
        #        self.error("DELETE requires a single parameter: <FILENAME>")
        #    else:
        #        await self.delete_file(cmd[1])

        elif cmd[0].upper() == "LIST":
            await self.list()

        elif cmd[0].upper() == "QUIT":
            await self.quit()

        elif cmd[0].upper() == "HELP":
            self.help()

        else:
            self.help()

    async def connect(self, address, port=12345):
        if self.writer:
            self.error("Already connected")
            return
        try:
            self.reader, self.writer = await asyncio.open_connection(address, port)
        except Exception as e:
            self.error(f"Failed to connect: {e}")
            return

        self.success(f"Successfully connected to {address}:{port}")

    async def disconnect(self):
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except ConnectionResetError:
            pass

        self.writer = None
        self.reader = None

    async def list(self):
        if self.writer is None:
            self.require_connection()
            return

        try:
            await self.send_json(
                {"method": "LIST",}
            )

            response = await self.recv_json()

            files = response["files"]

            if len(files) == 0:
                self.info("The server does not contain any files.")
            else:
                self.info("Files:")
                # self.info(response["files"])
                self.column_print(response["files"])

        except BrokenPipeError:
            self.require_connection()

    async def send_file(self, filename):
        if self.writer is None:
            self.require_connection()
            return

        if not os.path.exists(filename):
            self.error("Error: No such file exists")
            return

        with open(filename, "rb") as infile:
            contents = infile.read()

            # base64 encode the binary file
            contents = base64.b64encode(contents).decode("utf-8")

            try:
                await self.send_json(
                    {"method": "STORE", "filename": filename, "content": contents,},
                )

                self.success(
                    f"Successfully transferred {len(contents)} bytes to remote as {filename}"
                )

            except BrokenPipeError:
                self.require_connection()

    async def retrieve_string(self, filename):
        if self.writer is None:
            self.require_connection()
            return

        await self.send_json(
            {"method": "RETRIEVE", "filename": filename,}
        )

        response = await self.recv_json()

        error = response.get("error", None)

        if error:
            self.error(f"Failed to retrieve {filename}: {error}")
            return

        contents = response["content"]

        return base64.b64decode(contents).decode("utf-8")

    async def retrieve(self, filename):
        if self.writer is None:
            self.require_connection()
            return

        await self.send_json(
            {"method": "RETRIEVE", "filename": filename,}
        )

        response = await self.recv_json()

        error = response.get("error", None)

        if error:
            self.error(f"Failed to retrieve {filename}: {error}")
            return

        contents = response["content"]

        with open(filename, "wb") as outfile:
            # base64 decode from the request body
            contents = base64.b64decode(contents)
            outfile.write(contents)

        self.success(
            f"Successfully transferred {len(contents)} bytes from remote into {filename}"
        )

    async def delete_file(self, filename):
        if self.writer is None:
            self.require_connection()
            return

        await self.send_json(
            {"method": "DELETE", "filename": filename,}
        )

        response = await self.recv_json()

        error = response.get("error", None)

        if error:
            self.error(f"Failed to delete {filename}: {error}")
            return

        else:
            self.info("File deleted")

    async def quit(self):
        if self.writer is None:
            return

        await self.send_json(
            {"method": "QUIT",}
        )

    def help(self):
        self.info("Please enter a valid command.")
        self.info("Valid commands are:")
        self.info("\tCONNECT <IP> <PORT>")
        self.info("\tRETRIEVE <FILENAME>")
        self.info("\tLIST")
        self.info("\tQUIT")
