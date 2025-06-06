#!/bin/bash

set -euo pipefail  # Exit the script if any command fails or if an undefined variable is used

# Define helper functions
print_line() {
  local char="${1:--}"
  local count="${2:-70}"
  printf '%*s\n' "$count" '' | tr ' ' "$char"
}

section_divider() {
  local width=70
  local text="$1"

  print_line "=" "$width"
  # Wrap the input text to fit within the width and indent each line by 1 space
  echo "$text" | fold -s -w $((width - 1)) | while read -r line; do
    echo " $line"
  done
  print_line "=" "$width"
  
}

# Script logic

echo
echo
echo
echo
echo "   \ \      / _ \                __|          _)               "
echo "    \ \ \  /    /   _ \ \ \  \ / _| |  | (_-<  |   _ \    \    "
echo "     \_/\_/  _|_\ \___/  \_/\_/ _| \_,_| ___/ _| \___/ _| _|   "
echo '           |              |     |                         | '
echo '        _` |   _` | (_-<    \    _ \   _ \   _` |   _| _` | '
echo '      \__,_| \__,_| ___/ _| _| _.__/ \___/ \__,_| _| \__,_| '
echo
echo 
echo " This installs the local dashboard for WRowFusion... "
echo " ...putting you in pole position to control your workouts. "
echo " It's optimised for a Raspberry Pi, including the Zero models."
echo
echo
sleep 1.5
echo "            On your marks..."
sleep 1
echo "                 ... Get set..."
sleep 1
echo "                          ... Go!"
sleep 1
echo

## Create a temp directory to use for modifying templates
section_divider "Creating a temporary working directory and loading the installation configuration file..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/wrowfusion-dashboard.conf"
EXAMPLE_CONFIG_FILE="$SCRIPT_DIR/wrowfusion-dashboard_example.conf"

if [ ! -f "$CONFIG_FILE" ]; then
  echo
  echo " It looks like the configuration file is missing so the installation can't proceed."
  echo " Please create the file by copying and then editing the example configuration: "
  echo " - $EXAMPLE_CONFIG_FILE"
  echo " and saving it here:"
  echo " - $CONFIG_FILE"
  echo " Then run the install script again."
  echo
  echo " Exiting for now."
  exit 1
fi

# Temp dir for manipulating service files to local environment before deployment
TEMP_DIR=$(mktemp -d)
# Temp backup directory for storing existing installation before overwriting with the new installation
BACKUP_DIR="/var/tmp/wrowfusion-dashboard_backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_PATTERN="/var/tmp/wrowfusion-dashboard_backup_*"
MAX_BACKUPS=3

# Load configuration
source "$CONFIG_FILE"
echo
echo " Done"
echo

# Rollback function triggered on error
restore_backup() {
  if [ -d "$BACKUP_DIR" ]; then
    echo " - Install failed. Restoring from backup..."
    rm -rf "$APP_DIR"
    mv "$BACKUP_DIR" "$APP_DIR"
    echo " - Rollback complete."
    echo " - Exiting"
  elif [ -d "$APP_DIR" ]; then
    echo " - Install failed. Previous installation remains unchanged." >&2
  else
    echo " - Install failed. Exiting." >&2
  fi
}
trap restore_backup ERR

# Stop wrowfusion-dashboard service
section_divider "Stopping any wrowfusion-dashboard services if they are already running..."
echo

if systemctl is-active --quiet "wrowfusion-dashboard"; then
    echo " - Stopping existing wrowfusion-dashboard service..."
    sudo systemctl stop "wrowfusion-dashboard"
else
    echo " - wrowfusion-dashboard service is not running."
fi
echo
echo " Done."
echo

# Create the system user that will run the app
section_divider "Configuring a system user ${APP_USER} to run the application..."
echo

if ! id "$APP_USER" &>/dev/null; then
  if ! sudo useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"; then
      echo " - Failed to create user $APP_USER. Exiting."
      echo
      exit 1
  fi
fi
echo " Done."
echo

# Copy the application files
section_divider "Installing the application in the directory ${APP_DIR}..."
echo

if [ -d "$APP_DIR" ]; then
  echo " - Creating temporary backup of the existing $APP_DIR..."
  mkdir -p "$BACKUP_DIR"

  if cp -a "$APP_DIR/." "$BACKUP_DIR"; then
    echo
    echo " Done: Backup created at $BACKUP_DIR"
    echo
    echo " - Removing existing application directory..."
    rm -rf "$APP_DIR"
    echo
    echo " Done."
    echo
  else
    echo "Backup failed; aborting removal." >&2
    exit 1
  fi
fi

echo " - Copying application files to $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo cp -r "$SCRIPT_DIR"/* "$APP_DIR/"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
echo
echo " Done."
echo

# Install and configure Caddy
section_divider "Installing and configuring Caddy to give the dashboard a nice URL..."
echo

echo " - Updating system-package cache and installing caddy..."
sudo apt update
sudo apt install -y caddy
echo

echo " - Copying our Caddyfile and giving caddy access to our application..."
echo

# Add caddy user to the group that runs wrowfusion dashboard so that it can 
# read and write to the gunicorn unix socket
sudo usermod -aG wrowfusion caddy

cp "$APP_DIR/config/Caddyfile" "$TEMP_DIR/Caddyfile"
sed -i 's@#DASHBOARD_URL#@'"$DASHBOARD_URL"'@g' "$TEMP_DIR/Caddyfile"
sudo caddy fmt --overwrite "$TEMP_DIR/Caddyfile"
sudo install -o caddy -g caddy -m 0644 "$TEMP_DIR/Caddyfile" /etc/caddy/Caddyfile
rm -f "$TEMP_DIR/Caddyfile"
echo " Done."
echo

# Create the virtual environment
section_divider "Setting up a virtual environment to keep everything nicely contained..."
echo

sudo -u "$APP_USER" python3 -m venv "$APP_DIR"/venv
echo " Done."
echo

# Install python dependencies
section_divider "Installing python modules needed by WRowFusion..."
echo

sudo -u "$APP_USER" "$APP_DIR"/venv/bin/python3 -m pip install --upgrade --no-cache-dir pip setuptools wheel
sudo -u "$APP_USER" "$APP_DIR"/venv/bin/python3 -m pip install --no-cache-dir -r "$APP_DIR"/requirements.txt

echo " Done."
echo

## Set environment variables
section_divider "Configuring the variables for the local environment..."
echo

if [ -z "$FLASK_SECRET_KEY" ]; then
    echo " -No secret key found in config. Generating one..."
    FLASK_SECRET_KEY=$(openssl rand -hex 32)
    echo
fi

# Define required key-value pairs
declare -A REQUIRED_VARS=(
  ["WRFD_SECRET_KEY"]="$FLASK_SECRET_KEY"
  ["WRFD_WROWFUSION_API_SCHEME"]="$WROWFUSION_API_SCHEME"
  ["WRFD_WROWFUSION_API_HOST"]="$WROWFUSION_API_HOST"
  ["WRFD_WROWFUSION_API_PORT"]="$WROWFUSION_API_PORT"
  ["WRFD_WROWFUSION_WEBSOCKET_PORT"]="$WROWFUSION_WEBSOCKET_PORT"
  ["WRFD_DASHBOARD_URL"]="$DASHBOARD_URL"
  ["WRFD_LOG_DIR"]="$LOG_DIR"
)

sudo mkdir -p "$(dirname "$SERVICE_ENV_FILE_PATH")"
sudo chown "$APP_USER":"$APP_USER" "$(dirname "$SERVICE_ENV_FILE_PATH")"
# Ensure .env file exists
if [ ! -f "$SERVICE_ENV_FILE_PATH" ]; then
  touch "$SERVICE_ENV_FILE_PATH"
fi
sudo chown "$APP_USER":"$APP_USER" "$SERVICE_ENV_FILE_PATH"

# Check and add missing keys
for KEY in "${!REQUIRED_VARS[@]}"; do
  if ! grep -q "^${KEY}=" "$SERVICE_ENV_FILE_PATH"; then
    echo "${KEY}=${REQUIRED_VARS[$KEY]}" >> "$SERVICE_ENV_FILE_PATH"
  fi
done
echo " Done."
echo

## Configure logging
section_divider "Configuring logging..."
echo

echo " - Copying logger.conf..."
sudo -u "$APP_USER" cp "$APP_DIR"/config/logging_orig.conf "$APP_DIR"/config/logging.conf
echo 
echo " Done."
echo

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
  echo " - Creating the log directory: $LOG_DIR..."
  sudo mkdir -p "$LOG_DIR"
  sudo chown wrowfusion:wrowfusion "$LOG_DIR"
  sudo chmod 755 "$LOG_DIR"
  echo
  echo " Done."
  echo
fi

## Create WRowFusion dashboard systemd service
section_divider "Configuring WRowFusion Dashboard to launch at system start-up..."
echo
echo " - Launch the dashboard app at start up..."
cp "$APP_DIR"/config/wrowfusion-dashboard.service "$TEMP_DIR"/wrowfusion-dashboard.service
sed -i 's@#REPO_DIR#@'"$APP_DIR"'@g' "$TEMP_DIR"/wrowfusion-dashboard.service
sed -i 's@#APP_USER#@'"$APP_USER"'@g' "$TEMP_DIR"/wrowfusion-dashboard.service
sed -i 's@#SERVICE_ENV_FILE_PATH#@'"$SERVICE_ENV_FILE_PATH"'@g' "$TEMP_DIR"/wrowfusion-dashboard.service
sudo mv "$TEMP_DIR"/wrowfusion-dashboard.service /etc/systemd/system/wrowfusion-dashboard.service
sudo chmod 644 /etc/systemd/system/wrowfusion-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable wrowfusion-dashboard
echo
echo " Done."
echo

## (Re-) Start all the necessary services
section_divider "Starting everything up..."
echo

sudo systemctl start wrowfusion-dashboard
sudo systemctl reload caddy

echo " Done."
echo

## Clean up backups
section_divider "Cleaning up temporary backups..."
echo

# List backups sorted by newest first, skip the first $MAX_BACKUPS, then delete the rest
ls -td $BACKUP_PATTERN 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -rf
echo

## Installation complete!
section_divider "Installation complete!"
echo

exit 0