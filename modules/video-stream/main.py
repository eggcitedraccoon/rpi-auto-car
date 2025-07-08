# modules/video-stream/main.py
import paho.mqtt.client as mqtt
import json
import asyncio
import websockets
import subprocess
import numpy as np
import cv2


# BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
# TOPIC = "/video-stream"

# def on_message(client, userdata, msg):
#     command = json.loads(msg.payload.decode())
#     print(f"[video-stream] Received command: {command}")

# def main():
#     client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#     client.connect(BROKER_ADDRESS)
#     client.subscribe(TOPIC)
#     client.on_message = on_message
#
#     print("[video-stream] Listening for commands...")
#     client.loop_forever()
#
# if __name__ == "__main__":
#     main()

async def stream():
    uri = "ws://websocket-server:8765"
    width, height = 1920, 1080
    frame_size = width * height * 3

    # ffmpeg reads from udp://... where libcamera-vid is sending
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "udp://172.17.0.1:5000",  # docker host IP from container
        "-f", "image2pipe",
        "-pix_fmt", "bgr24",
        "-vcodec", "rawvideo",
        "-"
    ]
    ffmpeg_process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    async with websockets.connect(uri) as ws:
        while True:
            raw_frame = ffmpeg_process.stdout.read(frame_size)
            if not raw_frame:
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            await ws.send(jpeg.tobytes())
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(stream())
