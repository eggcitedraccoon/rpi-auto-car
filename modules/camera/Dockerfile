# modules/camera/Dockerfile

FROM balenalib/raspberrypi3-debian:latest

# Install dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    git \
    liblog4cpp5-dev \
    libssl-dev \
    libasound2-dev \
    libv4l-dev \
    v4l-utils \
    ffmpeg

# Clone and build v4l2rtspserver
RUN git clone https://github.com/mpromonet/v4l2rtspserver.git && \
    cd v4l2rtspserver && \
    cmake . && \
    make && \
    make install

# Expose RTSP port
EXPOSE 8554

# Run the server with default device /dev/video0
CMD ["v4l2rtspserver", "-W", "640", "-H", "480", "-F", "15", "/dev/video0"]
