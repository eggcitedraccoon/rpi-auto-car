# modules/ws-server/main.py
# import paho.mqtt.client as mqtt
# import json
#
# BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
# TOPIC = "/ws-server"
#
# def on_message(client, userdata, msg):
#     command = json.loads(msg.payload.decode())
#     print(f"[ws-server] Received command: {command}")
#
# def main():
#     client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#     client.connect(BROKER_ADDRESS)
#     client.subscribe(TOPIC)
#     client.on_message = on_message
#
#     print("[ws-server] Listening for commands...")
#     client.loop_forever()

import asyncio
import websockets
from typing import Set

clients: Set[websockets.WebSocketServerProtocol] = set()


async def handler(ws, path=None):
    client_addr = ws.remote_address
    print(f"[DEBUG] New connection from {client_addr}")

    clients.add(ws)
    print(f"[DEBUG] Client {client_addr} added. Total clients: {len(clients)}")

    try:
        async for message in ws:
            print(f"[DEBUG] Received message from {client_addr}: {len(message)} bytes")

            # Assume this is the streamer sending binary frame
            sent_count = 0
            for client in clients:
                if client != ws:
                    try:
                        await client.send(message)
                        sent_count += 1
                    except Exception as e:
                        print(f"[DEBUG] Error sending to client {client.remote_address}: {e}")

            print(f"[DEBUG] Message forwarded to {sent_count} clients")

    except websockets.exceptions.ConnectionClosed:
        print(f"[DEBUG] Connection closed by {client_addr}")
    except Exception as e:
        print(f"[DEBUG] Error handling client {client_addr}: {e}")
    finally:
        clients.remove(ws)
        print(f"[DEBUG] Client {client_addr} removed. Total clients: {len(clients)}")


async def main():
    print("[DEBUG] Starting WebSocket server on 0.0.0.0:8765")
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("[DEBUG] WebSocket server started and listening...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
