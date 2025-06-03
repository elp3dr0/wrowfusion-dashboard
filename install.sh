#!/bin/bash

#########################################################################
# wrowfusion will be installed in the following directory. This script
# will create the directory if it doesn't already exist. (Do not include
# a trailing slash / )
app_dir="/opt/wrowfusion-dashboard"

# The application will be run on startup by the following system user.
# This script will create this system user.
app_user="wrowfusion"
#########################################################################

set -e

echo "----------------------------------------------------"
echo " Installing Caddy..."
echo "----------------------------------------------------"

sudo apt update
sudo apt install -y caddy

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Configure system user ${app_user}"
echo "----------------------------------------------"
echo " "

if ! id "$app_user" &>/dev/null; then
  if ! sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$app_user"; then
      echo "Failed to create user $app_user. Exiting."
      exit 1
  fi
fi

#echo " Done."
#echo " "
#echo "----------------------------------------------------"
#echo " Creating dashboard directory and copying HTML files..."
#echo "----------------------------------------------------"

#sudo mkdir -p /var/www/wrowfusion-dashboard

# Copy your dashboard HTML into that directory
#sudo cp ./src/index.html /var/www/wrowfusion-dashboard/index.html

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Install the application in the directory:"
echo " ${app_dir}"
echo "----------------------------------------------"
echo " "


echo " Cleaning any existing $app_dir..."
sudo rm -rf "$app_dir"/*

sudo mkdir -p "$app_dir"

echo " Done."

echo " Copying application files to $app_dir..."
script_dir=$(cd "$(dirname "$0")" && pwd)
sudo cp -r "$script_dir"/src/* "$app_dir/"
sudo chown -R "$app_user:$app_user" "$app_dir"

echo " Done."
echo " "
echo "----------------------------------------------------"
echo " Copying Caddyfile to serve dashboard..."
echo "----------------------------------------------------"

sudo cp ./config/Caddyfile /etc/caddy/Caddyfile
#sudo caddy fmt --overwrite /etc/caddy/Caddyfile

echo " Done."
echo " "
echo "----------------------------------------------------"
echo " Reloading Caddy service..."
echo "----------------------------------------------------"

sudo systemctl reload caddy

echo " Done."
echo " "
echo "Caddy installed and configured to serve WRowFusion dashboard."