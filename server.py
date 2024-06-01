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

async def broadcast(data):
    disconnect_clients = []
    for client in clients:
        try:
            await client.send(json.dumps(data))
        except Exception as e:
            print(f"Error sending to client {clients[client]['id']}: {str(e)}")
            disconnect_clients.append(client)
    for client in disconnect_clients:
        clients.pop(client, None)

@app.websocket('/ws')
async def ws():
    global clients
    ws = websocket._get_current_object()
    
    ip = websocket.headers.get('X-Real-IP', websocket.remote_addr)
    user_agent = websocket.headers.get('User-Agent')
    client_id = str(uuid.uuid4())
    
    connection_info = {
        'id': client_id,
        'ip': ip,
        'user_agent': user_agent,
        'timestamp': datetime.now().isoformat()
    }
    clients[ws] = connection_info
    print("Client connected:", connection_info)
    print_current_clients()

    await websocket.send(json.dumps({'type': 'client_id', 'id': client_id}))
    await broadcast({'type': 'clients', 'clients': list(clients.values())})

    try:
        while True:
            message = await websocket.receive()
            data = json.loads(message)
            if data.get('type') == 'request_clients':
                await websocket.send(json.dumps({'type': 'clients', 'clients': list(clients.values())}))
            else:
                print(f"Received message from client {clients[ws]['id']}: {message}")
                await broadcast(data)
    except asyncio.CancelledError:
        pass
    finally:
        clients.pop(ws, None)
        await broadcast({'type': 'clients', 'clients': list(clients.values())})
        print("Client disconnected:", connection_info)
        print_current_clients()

def print_current_clients():
    print("\nCurrent Clients:")
    for client, info in clients.items():
        print(info)
    print("\n")

if __name__ == '__main__':
    app.run(port=8000)

