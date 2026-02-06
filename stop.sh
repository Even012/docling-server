#!/bin/bash

# Stop script for Docling Celery worker

# Detect compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose not found."
    exit 1
fi

cd "$(dirname "$0")"
$COMPOSE_CMD down

echo "Docling stopped."
