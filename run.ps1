#!/bin/bash
# Script to run the Flask backend on Windows (PowerShell)

# Default to development environment
$env:FLASK_ENV_DEFAULT = "development"
$env:FLASK_DEBUG_DEFAULT = "1"
$env:FLASK_PORT_DEFAULT = "12001"

# Use existing environment variables if set, otherwise use defaults
if (-not $env:FLASK_ENV) { $env:FLASK_ENV = $env:FLASK_ENV_DEFAULT }
if (-not $env:FLASK_DEBUG) { $env:FLASK_DEBUG = $env:FLASK_DEBUG_DEFAULT }
if (-not $env:FLASK_PORT) { $env:FLASK_PORT = $env:FLASK_PORT_DEFAULT }

# Path to the Flask app (relative to this script in the project root)
$env:FLASK_APP_PATH = "FlaskBackend\app.py"

# Path to the virtual environment (relative to this script in the project root)
$env:VENV_PATH = "code"

# Activate virtual environment if it exists
if (Test-Path "$env:VENV_PATH\Scripts\Activate.ps1") {
  Write-Host "Activating Python virtual environment from $($env:VENV_PATH)..."
  . "$env:VENV_PATH\Scripts\Activate.ps1"
} else {
  Write-Host "Virtual environment not found at $env:VENV_PATH\Scripts\Activate.ps1."
  Write-Host "Please ensure it's set up by running the following commands from the project root:"
  Write-Host "  python -m venv $($env:VENV_PATH)"
  Write-Host "  .\$($env:VENV_PATH)\Scripts\Activate.ps1"
  Write-Host "  pip install -r FlaskBackend\requirements.txt"
  Write-Host ""
  Write-Host "If Python is not found, make sure it's installed and added to your PATH."
  exit 1
}

# Set environment variables for Flask
$env:FLASK_APP = $env:FLASK_APP_PATH
# FLASK_ENV, FLASK_DEBUG, and FLASK_PORT are already set above and will be read by app.py

Write-Host "Starting Flask app..."
Write-Host "  FLASK_APP: $($env:FLASK_APP)"
Write-Host "  FLASK_ENV: $($env:FLASK_ENV)"
Write-Host "  FLASK_DEBUG: $($env:FLASK_DEBUG)"
Write-Host "  FLASK_PORT: $($env:FLASK_PORT) (app.py will use this from environment)"
Write-Host ""

# Run the Flask app using python directly, as app.py has a __main__ block
python "$env:FLASK_APP_PATH"

# To use 'flask run' command instead (ensure FLASK_APP is set as above):
# flask run --host=0.0.0.0 --port=$env:FLASK_PORT

# Deactivation of venv is usually not needed as the script/shell session ends.
# If you were to continue in the same PowerShell window:
# if (Get-Command deactivate -ErrorAction SilentlyContinue) {
#   deactivate
# }
