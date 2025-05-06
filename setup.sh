#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Get the directory where the script is located
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Define paths relative to the script's directory
VENV_DIR="$SCRIPT_DIR/.env"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# --- Check and install python3-venv if necessary ---
# Check if python3 -m venv works, if not, try to install python3-venv
if ! python3 -m venv --help &> /dev/null; then
    echo "python3 venv module not found. Attempting to install python3-venv..."
    # Check if apt exists (Debian/Ubuntu)
    if command -v apt &> /dev/null; then
        echo "Using apt package manager."
        # Check if sudo is needed (running as non-root)
        if [ "$(id -u)" -ne 0 ]; then
            SUDO_CMD="sudo"
        else
            SUDO_CMD=""
        fi
        $SUDO_CMD apt-get update && $SUDO_CMD apt-get install -y python3-venv
        if [ $? -ne 0 ]; then
            echo "Error: Failed to install python3-venv using apt."
            echo "Please install it manually for your system and rerun this script."
            exit 1
        fi
    else
        # Add checks for other package managers like yum, dnf if needed
        echo "Warning: apt package manager not found. Cannot automatically install python3-venv."
        echo "Please ensure python3's venv module is installed manually and rerun this script."
        # Optionally exit here if venv is strictly required
        # exit 1
    fi
    # Verify installation
    if ! python3 -m venv --help &> /dev/null; then
         echo "Error: python3-venv installation failed or venv module still not available."
         exit 1
    fi
    echo "python3-venv installed successfully."
fi
# --- End of venv check ---


# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment in $VENV_DIR..."
  # Create the virtual environment using python3's venv module
  python3 -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment."
    exit 1
  fi
else
  echo "Virtual environment '$VENV_DIR' already exists."
fi

# Activate the virtual environment using its absolute path
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
  echo "Error: Failed to activate virtual environment."
  exit 1
fi

# Check if requirements.txt exists using its absolute path
if [ -f "$REQUIREMENTS_FILE" ]; then
  echo "Installing requirements from $REQUIREMENTS_FILE..."
  # Install requirements using pip
  pip install -r "$REQUIREMENTS_FILE"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements."
    deactivate
    exit 1
  fi
  echo "Requirements installed successfully."
else
  echo "Warning: $REQUIREMENTS_FILE not found. Skipping installation of requirements."
fi

echo "To activate the virtual environment, run 'source $VENV_DIR/bin/activate'."
echo "To deactivate, run 'deactivate'."
