from quart import Quart, websocket, send_from_directory
import asyncio
import json
import uuid

app = Quart(__name__)

clients = {}

@app.route('/')
async def index():
    return await send_from_directory('static', 'client.html')

@app.websocket('/ws')
async def ws():
    client_id = str(uuid.uuid4())
    clients[client_id] = websocket

    await websocket.send(json.dumps({'type': 'client_id', 'id': client_id}))
    await notify_clients()

    try:
        while True:
            message = await websocket.receive()
            data = json.loads(message)

            target = data.get('target')
            if target and target in clients:
                await clients[target].send(message)
    except:
        del clients[client_id]
        await notify_clients()

async def notify_clients():
    client_list = [{'id': client_id} for client_id in clients]
    message = json.dumps({'type': 'clients', 'clients': client_list})
    await asyncio.gather(*(client.send(message) for client in clients.values()))

if __name__ == '__main__':
    app.run(port=8000)
