#!/bin/bash

# Docling Docker Setup Script

set -e

echo "=== Docling Celery Worker Setup ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed."
    echo ""
    echo "To install Docker, run:"
    echo "  sudo apt update"
    echo "  sudo apt install -y docker.io docker-compose"
    echo "  sudo systemctl enable docker"
    echo "  sudo systemctl start docker"
    echo "  sudo usermod -aG docker $USER"
    echo ""
    echo "After installation, log out and log back in, then run this script again."
    exit 1
fi

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "Warning: Your user is not in the docker group."
    echo "You may need to run: sudo usermod -aG docker $USER"
    echo "Then log out and log back in."
    echo ""
fi

# Check if docker-compose or docker compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: Neither docker-compose nor 'docker compose' is available."
    echo "Please install docker-compose: sudo apt install docker-compose"
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

# Create directories if they don't exist
mkdir -p documents output

# Start the service
echo "Starting Docling worker containers..."
$COMPOSE_CMD up -d

echo ""
echo "=== Docling worker is now running! ==="
echo ""
echo "Note:"
echo "  - This repo runs Docling as a Celery worker (no HTTP API/UI)."
echo "  - Configure broker via CELERY_BROKER_URL to match your app."
echo ""
echo "Useful commands:"
echo "  View logs:    $COMPOSE_CMD logs -f"
echo "  Stop:         $COMPOSE_CMD down"
echo "  Restart:      $COMPOSE_CMD restart"
echo "  Status:       $COMPOSE_CMD ps"
echo ""
