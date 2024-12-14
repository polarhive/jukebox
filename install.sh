#!/bin/bash

pause() {
  echo "Press Enter to proceed."
  read
  clear
}

venv_path="$HOME/.local/bin/jukebox-fm/.venv"

check_package() {
  local pkg=$1
  local pkg_name=$2
  if ! command -v "$pkg" > /dev/null 2>&1; then
    echo "Error: Please install $pkg_name using your package manager."
    exit 1
  fi
}

setup_venv() {
  if [ ! -d "$venv_path" ]; then
    echo "Creating virtual environment at $venv_path..."
    python -m venv "$venv_path"
  fi

  source "$venv_path/bin/activate"
  pip install --upgrade pip jukebox-fm
  clear
}

copy_config_files() {
  local src_dir="docs/."
  local dest_dir="$HOME"
  cp -r "$src_dir" "$dest_dir"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to copy configuration files. Check permissions and paths."
    exit 1
  fi
  echo "Configuration files setup complete."
}

clear
echo "Setup starting!"
sleep 1
pause

echo "Checking required system packages..."
sleep 1
check_package "python" "Python"
check_package "mpc" "MPC"
check_package "mpd" "MPD"
check_package "ncmpcpp" "ncmpcpp"
check_package "ffmpeg" "FFmpeg"
pause

setup_venv
echo "Virtual environment setup complete."
pause

copy_config_files
pause

if ! systemctl --user enable --now mpd; then
  echo "Error: Failed to enable/start MPD. Ensure correct permissions and a valid systemd user environment."
  exit 1
fi

echo "MPD service started successfully."
pause

echo "Running jukebox-fm..."
source "$venv_path/bin/activate"
if ! python -m jukebox_fm.jukebox; then
  echo "Error: Failed to execute jukebox-fm."
  exit 1
fi

clear

echo "Setup completed successfully!"
sleep 1
clear
echo "Now opening: ncmpcpp -- remember to press 'Enter' to start playing and 'p' to pause."
sleep 5

ncmpcpp -q

echo "Goodbye!"
