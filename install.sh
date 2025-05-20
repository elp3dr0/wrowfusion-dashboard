#!/bin/bash
set -e

echo "----------------------------------------------------"
echo " Installing Caddy..."
echo "----------------------------------------------------"

sudo apt update
sudo apt install -y caddy

echo "----------------------------------------------------"
echo " Creating dashboard directory and copying HTML files..."
echo "----------------------------------------------------"

sudo mkdir -p /var/www/wrowfusion-dashboard

# Copy your dashboard HTML into that directory
sudo cp ./src/index.html /var/www/wrowfusion-dashboard/index.html

echo "----------------------------------------------------"
echo " Copying Caddyfile to serve dashboard..."
echo "----------------------------------------------------"

sudo cp ./src/Caddyfile /etc/caddy/Caddyfile

echo "----------------------------------------------------"
echo " Reloading Caddy service..."
echo "----------------------------------------------------"

sudo systemctl reload caddy

echo "Caddy installed and configured to serve WRowFusion dashboard."