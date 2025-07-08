#!/bin/bash

# Check if module name is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <module_name>"
    exit 1
fi

# Create module directory
MODULE_NAME="$1"
mkdir -p "$MODULE_NAME"

# Create requirements.txt
cat << EOF > "$MODULE_NAME/requirements.txt"
# modules/$MODULE_NAME/requirements.txt
paho-mqtt
EOF

# Create main.py
cat << EOF > "$MODULE_NAME/main.py"
# modules/$MODULE_NAME/main.py
import paho.mqtt.client as mqtt
import json

BROKER_ADDRESS = "mqtt-broker"  # container name in docker-compose.yml
TOPIC = "/$MODULE_NAME"

def on_message(client, userdata, msg):
    command = json.loads(msg.payload.decode())
    print(f"[$MODULE_NAME] Received command: {command}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER_ADDRESS)
    client.subscribe(TOPIC)
    client.on_message = on_message

    print("[$MODULE_NAME] Listening for commands...")
    client.loop_forever()

if __name__ == "__main__":
    main()
EOF

# Create Dockerfile
cat << EOF > "$MODULE_NAME/Dockerfile"
# modules/$MODULE_NAME/Dockerfile

FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py ./
CMD ["python","-u", "main.py"]
EOF

cat << EOF >> "../shared/module.list"
module:$MODULE_NAME
EOF

echo "Module '$MODULE_NAME' created successfully!"
