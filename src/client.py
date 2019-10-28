#!/bin/python

#from gui import ClientGUI

import common

import asyncio


async def main():
    reader, writer = await asyncio.open_connection('127.0.0.1', 12345)

    await common.send_json(writer, {
        "method": "CONNECT",
        "username": "john",
        "hostname": "127.0.0.1", 
        "speed": "dial-up", 
        "files": [{
            "filename": "meme.png",
        }]
    })

    response = await common.recv_json(reader)

    print(response)

if __name__ == "__main__":
    
    asyncio.run(main())
    
    
    #client = ClientGUI()
