# modules/video_stream/main.py
import paho.mqtt.client as mqtt
import json
import asyncio
import websockets
import subprocess
import numpy as np
import cv2
import signal

# BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
# TOPIC = "/video_stream"

# def on_message(client, userdata, msg):
#     command = json.loads(msg.payload.decode())
#     print(f"[video_stream] Received command: {command}")

# def main():
#     client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
#     client.connect(BROKER_ADDRESS)
#     client.subscribe(TOPIC)
#     client.on_message = on_message
#
#     print("[video_stream] Listening for commands...")
#     client.loop_forever()
#
# if __name__ == "__main__":
#     main()

async def stream():
    uri = "ws://websocket-server:8765"
    width, height = 1920, 1080
    frame_size = width * height * 3  # bgr24 = 3 bytes per pixel

    # Start libcamera-vid
    libcamera_process = subprocess.Popen([
        "libcamera-vid",
        "-t", "0",
        "--inline",
        "--width", str(width),
        "--height", str(height),
        "--framerate", "30",
        "--codec", "h264",
        "-o", "udp://127.0.0.1:5000"
    ])

    try:
        # Start ffmpeg to convert H264 UDP to raw video frames
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", "udp://127.0.0.1:5000",
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
                    print("No frame received.")
                    break

                frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    print("JPEG encoding failed.")
                    continue

                await ws.send(jpeg.tobytes())
                await asyncio.sleep(0)  # yield control

    except Exception as e:
        print(f"Stream error: {e}")

    finally:
        # Cleanup
        libcamera_process.send_signal(signal.SIGINT)
        libcamera_process.wait()
        ffmpeg_process.terminate()
        ffmpeg_process.wait()


if __name__ == "__main__":
    asyncio.run(stream())
