from quart import Quart, websocket, send_from_directory
import asyncio
from datetime import datetime
import json
import uuid

app = Quart(__name__)

clients = {}

@app.route('/')
async def index():
    return await send_from_directory('static', 'client.html')

@app.websocket('/ws')
async def ws():
    # TODO
    pass

if __name__ == '__main__':
    app.run(port=8000)

