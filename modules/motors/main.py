# modules/motors/main.py

import json
import paho.mqtt.client as mqtt

BROKER_ADDRESS = "mqtt-broker"
TOPIC = "/planner/output"

def on_message(client, userdata, msg):
    command = json.loads(msg.payload.decode())
    print(f"[motors] Received command: {command}")

def main():
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS)
    client.subscribe(TOPIC)
    client.on_message = on_message

    print("[motors] Listening for commands...")
    client.loop_forever()

if __name__ == "__main__":
    main()
