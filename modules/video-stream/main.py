# modules/video-stream/main.py
import paho.mqtt.client as mqtt
import json
import asyncio
import websockets
import subprocess
import numpy as np
import cv2
import os
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger('video-stream')
import logging
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VideoStreamManager:
    def __init__(self,
                 udp_url="udp://172.17.0.1:5000",
                 ws_url="ws://ws-server:8765",
                 test_images_dir="/app/testImages",
                 stream_check_timeout=5,
                 test_image_interval=1 / 30,  # 30fps default
                 width=1920,
                 height=1080):
        self.udp_url = udp_url
        self.ws_url = ws_url
        self.test_images_dir = test_images_dir
        self.stream_check_timeout = stream_check_timeout
        self.test_image_interval = test_image_interval
        self.width = width
        self.height = height
        self.frame_size = width * height * 3

    def check_stream_exists(self):
        """Check if UDP stream exists by trying to read from it with timeout"""
        logger.info(f"Checking for UDP stream at {self.udp_url}...")

        ffmpeg_cmd = [
            "ffmpeg",
            "-timeout", str(self.stream_check_timeout * 1000000),  # microseconds
            "-i", self.udp_url,
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-frames:v", "1",  # Only try to get 1 frame
            "-"
        ]

        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for process to complete with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.stream_check_timeout + 2)

                if process.returncode == 0 and stdout and len(stdout) >= self.frame_size:
                    logger.info("UDP stream detected and working")
                    return True
                else:
                    logger.info("UDP stream not available - no data received")
                    return False

            except subprocess.TimeoutExpired:
                logger.info(f"UDP stream check timed out after {self.stream_check_timeout} seconds")
                process.kill()
                process.wait()
                return False

        except Exception as e:
            logger.error(f"Failed to start ffmpeg process: {e}")
            return False

    def get_test_images(self):
        """Get list of test images from the mounted directory"""
        test_images = []
        if os.path.exists(self.test_images_dir):
            for i in range(1, 12):  # test1.jpg to test11.jpg
                img_path = os.path.join(self.test_images_dir, f"test{i}.jpg")
                if os.path.exists(img_path):
                    test_images.append(img_path)
            logger.info(f"Found {len(test_images)} test images")
        else:
            logger.warning(f"Test images directory {self.test_images_dir} not found")
        return test_images

    async def stream_from_udp(self, ws):
        """Stream video from UDP source"""
        logger.info("Starting UDP stream...")

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", self.udp_url,
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

        frame_count = 0
        while True:
            raw_frame = ffmpeg_process.stdout.read(self.frame_size)
            if not raw_frame:
                logger.warning("UDP stream ended or interrupted")
                break

            frame = np.frombuffer(raw_frame, np.uint8).reshape((self.height, self.width, 3))
            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            await ws.send(jpeg.tobytes())
            frame_count += 1

            if frame_count % 300 == 0:  # Log every 10 seconds at 30fps
                logger.info(f"Streamed {frame_count} frames from UDP")

            await asyncio.sleep(0)

        ffmpeg_process.terminate()

    async def stream_test_content(self, ws):
        """Stream test images and send test messages"""
        logger.info("Starting test content mode...")

        # Send initial test message
        test_message = "WebSocket test - no UDP stream detected, sending test content"
        await ws.send(test_message.encode())
        print(f"Sent test message: {test_message}")

        test_images = self.get_test_images()

        if not test_images:
            # If no test images, send periodic test messages
            logger.info("No test images found, sending periodic test messages")
            message_count = 0
            while True:
                message = f"Test message #{message_count + 1} - WebSocket connection active"
                await ws.send(message.encode())
                print(f"Sent: {message}")
                message_count += 1
                await asyncio.sleep(self.test_image_interval)
        else:
            # Cycle through test images
            logger.info(f"Cycling through {len(test_images)} test images")
            image_index = 0
            frame_count = 0

            while True:
                try:
                    img_path = test_images[image_index]
                    frame = cv2.imread(img_path)

                    if frame is not None:
                        # Resize to target dimensions if needed
                        frame = cv2.resize(frame, (self.width, self.height))

                        ret, jpeg = cv2.imencode('.jpg', frame)
                        if ret:
                            await ws.send(jpeg.tobytes())
                            frame_count += 1

                            if frame_count % 30 == 0:  # Log every second at 30fps
                                print(f"Sent test image: {os.path.basename(img_path)} (frame {frame_count})")

                    # Move to next image
                    image_index = (image_index + 1) % len(test_images)

                    # Send occasional test message
                    if frame_count % 150 == 0:  # Every 5 seconds at 30fps
                        message = f"Test mode active - cycled through {frame_count} test frames"
                        await ws.send(message.encode())
                        print(f"Status: {message}")

                    await asyncio.sleep(self.test_image_interval)

                except Exception as e:
                    logger.error(f"Error processing test image {img_path}: {e}")
                    image_index = (image_index + 1) % len(test_images)
                    await asyncio.sleep(self.test_image_interval)


async def stream():
    """Main streaming function with automatic fallback"""
    # Initialize the stream manager
    stream_manager = VideoStreamManager(
        stream_check_timeout=5,  # 5 seconds to check for stream
        test_image_interval=1 / 30,  # 30fps for test images
    )

    # Check if UDP stream exists
    stream_exists = stream_manager.check_stream_exists()

    # Connect to WebSocket
    async with websockets.connect(stream_manager.ws_url) as ws:
        logger.info(f"Connected to WebSocket at {stream_manager.ws_url}")

        if stream_exists:
            logger.info("UDP stream available - starting live streaming")
            await stream_manager.stream_from_udp(ws)
        else:
            logger.info("No UDP stream - starting test content mode")
            await stream_manager.stream_test_content(ws)


# Alternative function with configurable parameters
async def stream_with_config(udp_url="udp://172.17.0.1:5000",
                             ws_url="ws://ws-server:8765",
                             test_images_dir="/app/testImages",
                             stream_check_timeout=5,
                             test_fps=30):
    """Stream function with configurable parameters"""
    stream_manager = VideoStreamManager(
        udp_url=udp_url,
        ws_url=ws_url,
        test_images_dir=test_images_dir,
        stream_check_timeout=stream_check_timeout,
        test_image_interval=1 / test_fps,
    )

    stream_exists = stream_manager.check_stream_exists()

    async with websockets.connect(stream_manager.ws_url) as ws:
        logger.info(f"Connected to WebSocket at {stream_manager.ws_url}")

        if stream_exists:
            await stream_manager.stream_from_udp(ws)
        else:
            await stream_manager.stream_test_content(ws)


# Example usage:
# asyncio.run(stream())
#
# Or with custom settings:
# asyncio.run(stream_with_config(
#     stream_check_timeout=10,    # Wait 10 seconds for stream
#     test_fps=15,               # 15fps for test images
#     test_images_dir="/custom/path"
# ))
if __name__ == "__main__":
    asyncio.run(stream())
