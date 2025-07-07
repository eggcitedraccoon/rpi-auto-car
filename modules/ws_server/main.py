# modules/ws_server/main.py
# import paho.mqtt.client as mqtt
# import json
#
# BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
# TOPIC = "/ws_server"
#
# def on_message(client, userdata, msg):
#     command = json.loads(msg.payload.decode())
#     print(f"[ws_server] Received command: {command}")
#
# def main():
#     client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#     client.connect(BROKER_ADDRESS)
#     client.subscribe(TOPIC)
#     client.on_message = on_message
#
#     print("[ws_server] Listening for commands...")
#     client.loop_forever()

import asyncio
import websockets
from typing import Set

clients: Set[websockets.WebSocketServerProtocol] = set()

async def handler(ws, path):
    clients.add(ws)
    try:
        async for message in ws:
            # Assume this is the streamer sending binary frame
            for client in clients:
                if client != ws:
                    await client.send(message)
    finally:
        clients.remove(ws)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
