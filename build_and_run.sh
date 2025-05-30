#!/bin/bash

docker compose down

docker compose up --build --no-attach mqtt-broker