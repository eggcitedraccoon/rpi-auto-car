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
* **Orchestrator Module (orch):** Publishes driving commands.
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

## 📋 License

MIT License
