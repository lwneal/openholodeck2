from quart import Quart, websocket, jsonify, send_from_directory
import asyncio

app = Quart(__name__)

clients = set()

@app.route('/')
async def index():
    return await send_from_directory('static', 'client.html')

@app.route('/<path:path>')
async def static_files(path):
    return await send_from_directory('static', path)

@app.websocket('/ws')
async def ws():
    global clients
    clients.add(websocket._get_current_object())
    print("Client connected")
    try:
        while True:
            data = await websocket.receive()
            for client in clients:
                if client != websocket._get_current_object():
                    await client.send(data)
    except asyncio.CancelledError:
        clients.remove(websocket._get_current_object())
        print("Client disconnected")
        raise

if __name__ == '__main__':
    app.run(port=8000)
