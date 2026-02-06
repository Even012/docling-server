# Docling Celery Worker (Docker Compose)

This setup runs **Docling conversions as a Celery task**, backed by **Redis**. It does **not** run the `docling-serve` HTTP server/UI.

## Prerequisites

Make sure Docker is installed on your system:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

**Important**: After adding your user to the docker group, log out and log back in for the changes to take effect.

## Quick Start

### Option 1: Use the setup script (recommended for first time)
```bash
./setup.sh
```

### Option 2: Manual start
```bash
# Start the worker + broker
docker-compose up -d
# or if using newer Docker: docker compose up -d

# Stop the service
docker-compose down

# View logs
docker-compose logs -f
```

### Option 3: Use convenience scripts
```bash
./start.sh   # Start Docling
./stop.sh    # Stop Docling
```

## Access Points

There is **no HTTP endpoint** in this repo. Your app should enqueue the Celery task `docling.convert`.

## Features

- **Auto-restart**: Containers automatically restart unless manually stopped
- **Same Redis broker as your app**: Configure via `CELERY_BROKER_URL`
- **Volume mounts**:
  - `./documents` - Mount your input documents here (read-only)
  - `./output` - Output directory for processed documents

## Broker configuration

Both your app and the `docling-worker` container should use the **same** broker URL. The default points at the host machine's Redis (shared with `design_assistant_backend`):

```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
```

Inside Docker the container reaches the host via `host.docker.internal`, which is configured automatically in `docker-compose.yml`.

## Using Podman (Alternative to Docker)

If you prefer Podman over Docker:

```bash
# Install Podman
sudo apt install -y podman podman-compose

# Start with Podman Compose
podman-compose up -d

```

## Usage Examples

### Enqueue the Celery task

From any Python process configured with the same broker URL:

```bash
python -c "from docling_worker.tasks import convert; r = convert.delay(input='https://arxiv.org/pdf/2408.09869'); print(r.id)"
```

The worker writes outputs under `./output/<task-id>/`.

### Using the CLI directly (optional)

```bash
docling https://arxiv.org/pdf/2408.09869
```

## Troubleshooting

- Check container status: `docker ps -a | grep docling`
- View logs: `docker-compose logs docling-worker`
- Restart service: `docker-compose restart docling-worker`

## Documentation

For more information, visit:
- [Docling Documentation](https://docling-project.github.io/docling/)
- [Docling Serve Repository](https://github.com/docling-project/docling-serve)
