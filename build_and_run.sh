#!/bin/bash

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "Error: Current user is not in the docker group."
    echo "To fix this, run: sudo usermod -aG docker $USER"
    echo "Then log out and log back in, or run: newgrp docker"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker daemon is not running."

    # Check if Docker service unit exists
    if systemctl list-unit-files docker.service &> /dev/null; then
        echo "To start it, run: sudo systemctl start docker"
        echo "To enable it at boot, run: sudo systemctl enable docker"
    else
        echo "Docker service unit not found (docker.service)."
        echo "If you're using Docker Desktop, try starting it from the application menu."
        echo "For more detailed troubleshooting, run: ./docker_fix.sh"
    fi
    exit 1
fi

docker compose down

docker compose up --build --no-attach mqtt-broker
