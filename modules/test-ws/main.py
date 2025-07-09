# modules/test-ws/main.py
import paho.mqtt.client as mqtt
import json
import asyncio
import websockets

# BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
# TOPIC = "/test-ws"
#
# def on_message(client, userdata, msg):
#     command = json.loads(msg.payload.decode())
#     print(f"[test-ws] Received command: {command}")
#
# def main():
#     client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#     client.connect(BROKER_ADDRESS)
#     client.subscribe(TOPIC)
#     client.on_message = on_message
#
#     print("[test-ws] Listening for commands...")
#     client.loop_forever()

async def test():
    uri = "ws://video-stream:8765"
    async with websockets.connect(uri) as ws:
        await ws.send(b"hello camera feed")
        print("Sent test message")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test())
