#!/bin/bash

# --- Configuration ---
# Set the absolute path to your project directory.
PROJECT_DIR="/home/pi/QtPye-PPM-Controller"
# Set a high, unused display number for the virtual screen.
DISPLAY_NUM=99

# --- Cleanup ---
# Kill any leftover processes from a previous run to ensure a clean start.
echo "Cleaning up old processes..."
killall Xvfb > /dev/null 2>&1
killall x11vnc > /dev/null 2>&1
killall oversteer > /dev/null 2>&1
killall python3 > /dev/null 2>&1
sleep 1

# --- Virtual Display Setup ---
echo "Starting virtual display on :$DISPLAY_NUM..."
# Start the virtual framebuffer in the background.
# All graphical apps will be directed to this in-memory screen.
Xvfb :$DISPLAY_NUM -screen 0 1280x720x24 &

# Give Xvfb a moment to initialize.
sleep 2

# Set the DISPLAY environment variable for all subsequent commands in this script.
export DISPLAY=:$DISPLAY_NUM

# --- VNC Server ---
echo "Starting VNC server..."
# Start the VNC server in the background, pointing to our new virtual display.
# -forever keeps it running, -nopw allows connection without a password.
x11vnc -forever -nopw -quiet &

# --- Application Launch ---
# Navigate to the project directory.
cd "$PROJECT_DIR" || { echo "Failed to cd to project directory"; exit 1; }

# Activate the Python virtual environment if it exists.
if [ -d "venv" ]; then
  echo "Activating Python virtual environment..."
  source venv/bin/activate
fi

# Finally, run the main application using oversteer.
# This command will run in the foreground and keep the script alive.
echo "Launching Oversteer and QtPye-PPM-Controller..."
oversteer -p default -g "python3 main.py"

# --- Optional Cleanup on Exit ---
echo "Application closed. Shutting down virtual display..."
killall Xvfb
killall x11vnc

# How to Set Up Autostart
# This is the standard way to launch graphical applications on startup.
#
# 1.  Create a new file in the autostart directory using the `nano` text editor:
#
#     nano ~/.config/autostart/qtpye-ppm.desktop
#
# 2.  Copy and paste the following text into the editor:
#
#     [Desktop Entry]
#     Type=Application
#     Name=QtPye PPM Controller
#     Comment=Starts the PPM controller, Oversteer, and VNC server
#     Exec=/home/pi/QtPye-PPM-Controller/start_headless.sh
#     Terminal=false
#
