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

    # Create a black frame as a placeholder when no video is available
    black_frame = np.zeros((height, width, 3), np.uint8)
    ret, black_jpeg = cv2.imencode('.jpg', black_frame)
    black_jpeg_bytes = black_jpeg.tobytes() if ret else None

    # Flag to track if we're using the real video stream or placeholder
    using_placeholder = False
    ffmpeg_process = None

    global connected_clients

    while True:
        # Try to start or restart ffmpeg process if not running or using placeholder
        if ffmpeg_process is None or using_placeholder:
            try:
                # ffmpeg reads from udp://... where libcamera-vid is sending
                ffmpeg_cmd = [
                    "ffmpeg",
                    "-i", "udp://172.17.0.1:5000",  # docker host IP from container
                    "-f", "image2pipe",
                    "-pix_fmt", "bgr24",
                    "-vcodec", "rawvideo",
                    "-"
                ]

                # Try to start the ffmpeg process
                ffmpeg_process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL
                )

                logger.info("Started ffmpeg process to capture video frames")
                using_placeholder = False
            except Exception as e:
                logger.warning(f"Failed to start ffmpeg process: {e}")
                ffmpeg_process = None
                using_placeholder = True

        # If we have a valid ffmpeg process, try to read a frame
        if ffmpeg_process is not None and not using_placeholder:
            try:
                raw_frame = ffmpeg_process.stdout.read(frame_size)
                if not raw_frame:
                    logger.warning("No frame data received, switching to placeholder")
                    using_placeholder = True
                    continue

                frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 3))
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    logger.warning("Failed to encode frame to JPEG")
                    using_placeholder = True
                    continue

                jpeg_bytes = jpeg.tobytes()
            except Exception as e:
                logger.warning(f"Error processing video frame: {e}")
                using_placeholder = True
                continue
        else:
            # Use placeholder black frame
            if black_jpeg_bytes is None:
                logger.warning("No placeholder frame available")
                await asyncio.sleep(1)  # Longer delay when no frame is available
                continue

            jpeg_bytes = black_jpeg_bytes
            if not using_placeholder:
                logger.info("Using placeholder black frame")
                using_placeholder = True

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

        # Adjust sleep time based on whether we're using real video or placeholder
        await asyncio.sleep(0.01 if not using_placeholder else 1.0)  # Longer delay for placeholder

        # Periodically try to restart the video stream if using placeholder
        if using_placeholder and ffmpeg_process is not None:
            # Check if process is still running
            if ffmpeg_process.poll() is not None:
                ffmpeg_process = None
                logger.info("ffmpeg process terminated, will try to restart")

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
