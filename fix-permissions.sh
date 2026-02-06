#!/bin/bash

# Fix Docker permissions script

echo "=== Fixing Docker Permissions ==="
echo ""

# Check if user is in docker group
if ! groups | grep -q docker; then
    echo "Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo ""
    echo "✓ User added to docker group"
    echo ""
    echo "IMPORTANT: You need to log out and log back in for this to take effect."
    echo ""
    echo "Alternatively, you can use one of these methods:"
    echo "  1. Run: newgrp docker"
    echo "  2. Run: sg docker -c './start.sh'"
    echo "  3. Restart your terminal session"
    echo ""
else
    echo "✓ User is already in docker group"
    echo ""
    echo "If you still get permission errors, try:"
    echo "  - Log out and log back in"
    echo "  - Run: newgrp docker"
    echo ""
fi
