#!/bin/bash
set -e

echo "----------------------------------------------------"
echo " Installing Caddy..."
echo "----------------------------------------------------"

# Import official repo key
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo tee /usr/share/keyrings/caddy-stable-archive-keyring.gpg >/dev/null

# Add Caddy repo
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
  sudo tee /etc/apt/sources.list.d/caddy-stable.list

sudo apt update

# Install Caddy
sudo apt install -y caddy

echo "----------------------------------------------------"
echo " Creating dashboard directory and copying HTML files..."
echo "----------------------------------------------------"
# Create directory for your dashboard site
sudo mkdir -p /var/www/wrowfusion-dashboard

# Copy your dashboard HTML into that directory
# Assuming you run this script from the project root with index.html inside
sudo cp ./index.html /var/www/wrowfusion-dashboard/index.html

echo "----------------------------------------------------"
echo " Copying Caddyfile to serve dashboard..."
echo "----------------------------------------------------"

sudo cp .src/Caddyfile /etc/caddy/Caddyfile

echo "----------------------------------------------------"
echo " Reloading Caddy service..."
echo "----------------------------------------------------"

sudo systemctl reload caddy

echo "Caddy installed and configured to serve WRowFusion dashboard."
