import common
from asyncio import StreamReader, StreamWriter
import asyncio
import os
import base64
from typing import Dict

# filter out files with *.py extensions
def filter_files(path):
    _, extension = os.path.splitext(path[0])

    if extension == ".py":
        return False
    else:
        return True


class FTPServer:
    async def handle_file_request(
        self, request: Dict, reader: StreamReader, writer: StreamWriter
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

    async def run_forever(self, local_port):
        server = await asyncio.start_server(
            self.handle_request, "127.0.0.1", local_port
        )
        addr = server.sockets[0].getsockname()

        print("Server started")
        print(f"Waiting for file requests on {addr}")

        async with server:
            await server.serve_forever()

    async def handle_request(self, reader: StreamReader, writer: StreamWriter):
        while True:
            request = await common.recv_json(reader)

            print(request)

            if request is None:
                break

            if not request["method"]:
                print("Invalid Request: missing method field.")

            if request["method"].upper().startswith("LIST"):
                files = [f for f in os.listdir(".") if os.path.isfile(f)]
                file_sizes = [
                    common.sizeof_fmt(os.path.getsize(f))
                    for f in os.listdir(".")
                    if os.path.isfile(f)
                ]

                files = list(zip(files, file_sizes))

                files = filter(filter_files, files)

                files = list(files)

                await common.send_json(writer, {"files": files,})

            elif request["method"].upper().startswith("RETRIEVE"):
                filename = request["filename"]

                if not os.path.exists(filename):
                    await common.send_json(writer, {"error": "file does not exist"})
                    return

                with open(filename, "rb") as infile:
                    contents = infile.read()

                    # base64 encode the binary file
                    contents = base64.b64encode(contents).decode("utf-8")

                    await common.send_json(
                        writer, {"filename": filename, "content": contents}
                    )

            elif request["method"].upper().startswith("STORE"):
                filename = request["filename"]

                with open(filename, "wb") as outfile:
                    # base64 decode from the request body
                    contents = base64.b64decode(request["content"])
                    outfile.write(contents)

                # threaded_print("-> Store Complete")

            elif request["method"].upper().startswith("QUIT"):
                # threaded_print("-> Client disconnected via QUIT")
                pass

            elif request["method"].upper().startswith("DELETE"):

                filename = request["filename"]

                if not os.path.exists(filename):
                    await common.send_json(writer, {"error": "file does not exist"})
                else:
                    os.remove(filename)
                    await common.send_json(writer, {"success": "file removed"})

            else:
                await common.send_json(writer, {"error": "Unsupported command"})

        writer.close()
        await writer.wait_closed()
