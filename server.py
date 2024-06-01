from quart import Quart, websocket, send_from_directory
import asyncio
from datetime import datetime

app = Quart(__name__)

clients = {}

@app.route('/')
async def index():
    return await send_from_directory('static', 'client.html')

async def broadcast(data):
    disconnect_clients = []
    for client in clients:
        try:
            await client.send(data)
        except Exception as e:
            print(f"Error sending to client {clients[client]}: {str(e)}")
            disconnect_clients.append(client)
    for client in disconnect_clients:
        clients.pop(client, None)

async def broadcast_clients():
    client_list = [{'ip': info['ip'], 'user_agent': info['user_agent'], 'timestamp': info['timestamp']} for info in clients.values()]
    await broadcast({'type': 'clients', 'clients': client_list})

@app.websocket('/ws')
async def ws():
    global clients
    ws = websocket._get_current_object()
    
    ip = websocket.headers.get('X-Real-IP', websocket.remote_addr)
    user_agent = websocket.headers.get('User-Agent')
    connection_info = {
        'ip': ip,
        'user_agent': user_agent,
        'timestamp': datetime.now().isoformat()
    }
    clients[ws] = connection_info
    print("Client connected:", connection_info)
    print_current_clients()

    await broadcast_clients()

    try:
        while True:
            message = await websocket.receive()
            print(f"Received message from client {clients[ws]}: {message}")
            await broadcast(message)
    except asyncio.CancelledError:
        pass
    finally:
        clients.pop(ws, None)
        await broadcast_clients()
        print("Client disconnected:", connection_info)
        print_current_clients()

def print_current_clients():
    print("\nCurrent Clients:")
    for client, info in clients.items():
        print(info)
    print("\n")

if __name__ == '__main__':
    app.run(port=8000)
