from quart import Quart, websocket, send_from_directory
import asyncio
import json
import uuid

app = Quart(__name__)

clients = {}

@app.route('/')
async def index():
    return await send_from_directory('static', 'client.html')

@app.route('/rtc.js')
async def rtc():
    return await send_from_directory('static', 'rtc.js')

@app.websocket('/ws')
async def ws():
    client_id = str(uuid.uuid4())
    clients[client_id] = websocket

    await websocket.send(json.dumps({'type': 'client_id', 'id': client_id}))
    await notify_clients()

    # Start a background task to send periodic pings
    asyncio.create_task(periodic_ping(client_id))

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

async def periodic_ping(client_id):
    while client_id in clients:
        try:
            await clients[client_id].send(json.dumps({'type': 'ping', 'timestamp': str(uuid.uuid1())}))
        except:
            del clients[client_id]
            await notify_clients()
            break
        await asyncio.sleep(2)

if __name__ == '__main__':
    app.run(port=8000)
