#!/bin/bash

#########################################################################
# wrowfusion will be installed in the following directory. This script
# will create the directory if it doesn't already exist. (Do not include
# a trailing slash / )
app_dir="/opt/wrowfusion-dashboard"

# The application will be run on startup by the following system user.
# This script will create this system user.
app_user="wrowfusion"

dashboard_url="wrowfusion.local.example.com"
#########################################################################

set -e

echo "----------------------------------------------"
echo " Stop any existing wrowfusion-dashboard service."
echo "----------------------------------------------"
echo " "

if systemctl is-active --quiet "wrowfusion-dashboard"; then
    echo " Stopping existing wrowfusion-dashboard service..."
    sudo systemctl stop "wrowfusion-dashboard"
else
    echo " wrowfusion-dashboard is not running."
fi

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

echo " Done."
echo " "
echo "----------------------------------------------------"
echo " Installing Caddy..."
echo "----------------------------------------------------"

sudo apt update
sudo apt install -y caddy
# Add caddy user to the group that runs wrowfusion dashboard so that it can 
# read and write to the gunicorn unix socket
sudo usermod -aG wrowfusion caddy

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
echo "----------------------------------------------"
echo " Setting up virtual environment        "
echo "----------------------------------------------"
echo " "

sudo -u "$app_user" python3 -m venv "$app_dir"/venv

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Install python modules needed by WRowFusion"
echo "----------------------------------------------"
echo " "

sudo -u "$app_user" "$app_dir"/venv/bin/python3 -m pip install --upgrade --no-cache-dir pip setuptools wheel
sudo -u "$app_user" "$app_dir"/venv/bin/python3 -m pip install --no-cache-dir -r "$app_dir"/requirements.txt

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Configure logging for the local environment"
echo "----------------------------------------------"
echo " "

sudo -u "$app_user" cp "$app_dir"/config/logging_orig.conf "$app_dir"/config/logging.conf

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Start WRowFusion Dashboard when system boots"
echo "----------------------------------------------"
echo " "

sudo cp "$app_dir"/config/wrowfusion-dashboard.service /etc/systemd/system/wrowfusion-dashboard.service
sudo sed -i 's@#REPO_DIR#@'"$app_dir"'@g' /etc/systemd/system/wrowfusion-dashboard.service
sudo sed -i 's@#APP_USER#@'"$app_user"'@g' /etc/systemd/system/wrowfusion-dashboard.service
sudo chmod 644 /etc/systemd/system/wrowfusion-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable wrowfusion-dashboard

echo " Done."
echo " "
echo "----------------------------------------------"
echo " Restart services and run wrowfusion dashboard"
echo " service"
echo "----------------------------------------------"
echo " "

sudo systemctl start wrowfusion-dashboard


echo " Done."
echo " "
echo "----------------------------------------------------"
echo " Copying Caddyfile to serve dashboard..."
echo "----------------------------------------------------"

sudo cp ./config/Caddyfile /etc/caddy/Caddyfile
sudo sed -i 's@#DASHBOARD_URL#@'"$dashboard_url"'@g' /etc/caddy/Caddyfile
sudo caddy fmt --overwrite /etc/caddy/Caddyfile

echo " Done."
echo " "
echo "----------------------------------------------------"
echo " Reloading Caddy service..."
echo "----------------------------------------------------"

sudo systemctl reload caddy

echo " Done."
echo " "
echo "Caddy installed and configured to serve WRowFusion dashboard."