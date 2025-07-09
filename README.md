# Raspberry Pi Autonomous Car - Modular System

This project is a modular autonomous car system designed for the Raspberry Pi. It allows students to develop individual modules (e.g. object detection, lane detection) independently and integrate them seamlessly using Docker and MQTT.

## 🔧 Project Structure

```

rpi-autonomous-car/
├── modules/
│   ├── orch/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   └── motors/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
├── shared/
│   └── mqtt\_topics.md
├── docker-compose.yml
└── README.md

```

## 🚀 Getting Started

1️⃣ Clone the repository:
```bash
git clone https://github.com/yourusername/rpi-autonomous-car.git
cd rpi-autonomous-car
```

2️⃣ Build and run the containers:

```bash
docker-compose up --build
```

3️⃣ Check logs:

```bash
docker-compose logs -f
```

The orchestrator module (`orch`) publishes driving commands to the MQTT broker, and the motors module (`motors`) listens for those commands and prints them.

## 🤖 How It Works

* **MQTT Broker:** Manages message passing between modules.
* **Orchestrator Module (orchestrator):** Publishes driving commands.
* **Motors Module (motors):** Subscribes to commands and logs them.

## 📡 MQTT Topics

| Topic             | Description                                                 |
| ----------------- | ----------------------------------------------------------- |
| `/planner/output` | JSON messages with driving commands (e.g., steering angle). |

## ✨ Contributing

Feel free to fork the repo and add your own modules! Each module should:

* Have its own folder in `modules/`.
* Expose a Dockerfile, requirements.txt, and main.py.
* Use MQTT for communication.

## 🔍 Troubleshooting Docker Issues

For automatic diagnosis and fixing of Docker issues, run the included troubleshooting script:

```bash
# For basic checks:
./docker_fix.sh

# For full functionality (including fixing permissions):
sudo ./docker_fix.sh
```

If you prefer to troubleshoot manually, here are some common problems and solutions:

### Permission Denied Error

If you see an error like:
```
permission denied while trying to connect to the Docker daemon socket
```

This means your user doesn't have permission to access the Docker daemon. To fix this:

1. Add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

2. Log out and log back in, or run this command to apply the changes immediately:
   ```bash
   newgrp docker
   ```

### Docker Daemon Not Running

If Docker commands fail with errors about the daemon not running:

1. Check the status of the Docker daemon:
   ```bash
   sudo systemctl status docker
   ```

2. Start the Docker daemon if it's not running:
   ```bash
   sudo systemctl start docker
   ```

3. Enable the Docker daemon to start automatically at boot:
   ```bash
   sudo systemctl enable docker
   ```

### Docker Service Not Found

If you see an error like:
```
Failed to start docker.service: Unit docker.service not found.
```

This means the Docker service is not properly registered with systemd. This can happen if:

1. You're using Docker Desktop instead of Docker Engine
2. Docker was installed manually without systemd integration
3. Docker installation is incomplete or corrupted

To fix this issue:

1. If you're using Docker Desktop:
   - Start Docker Desktop from the application menu
   - Or use the systemctl user command if available:
     ```bash
     systemctl --user start docker-desktop
     ```

2. If you need Docker Engine with systemd:
   - Reinstall Docker with proper systemd integration:
     ```bash
     # Uninstall current Docker installation
     sudo apt purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-desktop

     # Install Docker Engine with systemd support
     curl -fsSL https://get.docker.com -o get-docker.sh
     sudo sh get-docker.sh
     ```

### Other Docker Issues

1. Check Docker logs for more information:
   ```bash
   sudo journalctl -u docker
   ```

2. Restart the Docker daemon:
   ```bash
   sudo systemctl restart docker
   ```

## 📋 License

MIT License
