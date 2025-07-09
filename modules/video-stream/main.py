# modules/video-stream/main.py
import paho.mqtt.client as mqtt
import json
import asyncio
import websockets
import subprocess
import numpy as np
import cv2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger('video-stream')

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

# Global set to track connected clients
connected_clients = set()

async def process_video_frames():
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

    logger.info("Started ffmpeg process to capture video frames")

    global connected_clients
    
    while True:
        raw_frame = ffmpeg_process.stdout.read(frame_size)
        if not raw_frame:
            logger.warning("No frame data received, breaking loop")
            break

        frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            logger.warning("Failed to encode frame to JPEG")
            continue

        jpeg_bytes = jpeg.tobytes()

        # Send frame to all connected clients
        if connected_clients:
            # Create a copy of the set to avoid modification during iteration
            clients_to_remove = set()
            
            for client in connected_clients:
                success = await send_frame(client, jpeg_bytes)
                if not success:
                    clients_to_remove.add(client)
            
            # Remove disconnected clients
            connected_clients -= clients_to_remove

        await asyncio.sleep(0.01)  # Small delay to prevent CPU overload

    logger.info("Video processing loop ended")

async def send_frame(websocket, frame_data):
    try:
        await websocket.send(frame_data)
        return True
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected during frame send: {websocket.remote_address}")
        return False
    except Exception as e:
        logger.error(f"Error sending frame: {e}")
        return False

async def handle_client(websocket, path=None):
    client_address = websocket.remote_address
    logger.info(f"New client connected: {client_address}")

    global connected_clients
    connected_clients.add(websocket)
    logger.info(f"Added client to connected_clients. Total clients: {len(connected_clients)}")

    try:
        # Keep the connection open
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"Client disconnected normally: {client_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"Client connection closed with error: {client_address}, {e}")
    except Exception as e:
        logger.error(f"Unexpected error with client {client_address}: {e}")
    finally:
        # Remove client from set when disconnected
        if websocket in connected_clients:
            connected_clients.remove(websocket)
            logger.info(f"Removed client from connected_clients. Remaining clients: {len(connected_clients)}")

async def main():
    # Start the websocket server
    host = "0.0.0.0"
    port = 8765

    # Start the websocket server
    async with websockets.serve(handle_client, host, port):
        logger.info(f"Websocket server started on {host}:{port}")
        await asyncio.Future()  # Run forever

    # Start video processing in the background
    video_task = asyncio.create_task(process_video_frames())

if __name__ == "__main__":
    logger.info("Starting video-stream module")
    asyncio.run(main())
