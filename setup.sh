#!/bin/bash

pause() {
  echo "Press Enter to proceed."
  read
  clear
}

repo_url="https://github.com/polarhive/jukebox/archive/refs/heads/main.tar.gz"
tarball="/tmp/jukebox-main.tar.gz"
extracted_dir="/tmp/jukebox-main"
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
    python3 -m venv "$venv_path"
  fi

  source "$venv_path/bin/activate"
  pip install --upgrade pip jukebox-fm
  clear
}

download_repo() {
  echo "Downloading the repository tarball to /tmp..."
  curl -fsSL "$repo_url" -o "$tarball"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to download tarball. Check your network connection."
    exit 1
  fi

  echo "Extracting tarball to /tmp..."
  mkdir -p "$extracted_dir"
  tar -xzf "$tarball" -C /tmp
  if [ $? -ne 0 ]; then
    echo "Error: Failed to extract tarball."
    exit 1
  fi
  clear
}

copy_config_files() {
  local src_dir="$extracted_dir/docs/."
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
check_package "python3" "python3"
check_package "mpc" "MPC"
check_package "mpd" "MPD"
check_package "ncmpcpp" "ncmpcpp"
check_package "ffmpeg" "FFmpeg"
pause

download_repo
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
if ! python3 -m jukebox_fm.jukebox; then
  echo "Error: Failed to execute jukebox-fm."
  exit 1
fi

clear

rm -rf "$tarball" "$extracted_dir"
echo "Setup completed successfully!"
sleep 1
clear
echo "Now opening: ncmpcpp"
sleep 1
echo "Remember to press 'Enter' to start playing and 'p' to pause."
sleep 4

ncmpcpp -q

echo "Goodbye!"
