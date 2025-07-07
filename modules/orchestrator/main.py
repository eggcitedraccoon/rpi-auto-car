# modules/orchestrator/main.py

import time
import json
import paho.mqtt.client as mqtt

BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
TOPIC = "/planner/output"


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_ADDRESS)
    print("[orchestrator] Connected to MQTT broker")
    count = 0
    while True:
        # Simulate sending steering angle (e.g., 0 = straight, -1 = left, 1 = right)
        command = {"steering_angle": count}
        client.publish(TOPIC, json.dumps(command))
        print(f"[orchestrator] Published command: {command}")
        count += 0.05
        if count > 1:
            count = -1
        time.sleep(5)

if __name__ == "__main__":
    main()
