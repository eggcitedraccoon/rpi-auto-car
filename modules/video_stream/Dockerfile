# modules/video_stream/Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcamera-apps \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python requirements
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY main.py ./

# Allow subprocess logging immediately
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "main.py"]
