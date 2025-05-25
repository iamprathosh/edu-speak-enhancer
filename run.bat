@echo off
REM Script to run the Flask backend on Windows (Command Prompt)

REM Default to development environment
set FLASK_ENV_DEFAULT=development
set FLASK_DEBUG_DEFAULT=1
set FLASK_PORT_DEFAULT=12001

REM Use existing environment variables if set, otherwise use defaults
if "%FLASK_ENV%"=="" (set FLASK_ENV=%FLASK_ENV_DEFAULT%)
if "%FLASK_DEBUG%"=="" (set FLASK_DEBUG=%FLASK_DEBUG_DEFAULT%)
if "%FLASK_PORT%"=="" (set FLASK_PORT=%FLASK_PORT_DEFAULT%)

REM Path to the Flask app (relative to this script in the project root)
set FLASK_APP_PATH=FlaskBackend\app.py

REM Path to the virtual environment (relative to this script in the project root)
set VENV_PATH=code

REM Activate virtual environment if it exists
if exist "%VENV_PATH%\Scripts\activate.bat" (
  echo Activating Python virtual environment from %VENV_PATH%...
  call "%VENV_PATH%\Scripts\activate.bat"
) else (
  echo Virtual environment not found at %VENV_PATH%\Scripts\activate.bat.
  echo Please ensure it's set up by running the following commands from the project root:
  echo   python -m venv %VENV_PATH%
  echo   %VENV_PATH%\Scripts\activate.bat
  echo   pip install -r FlaskBackend\requirements.txt
  echo.
  echo If Python is not found, make sure it's installed and added to your PATH.
  exit /b 1
)

REM Set environment variables for Flask
set FLASK_APP=%FLASK_APP_PATH%
REM FLASK_ENV, FLASK_DEBUG, and FLASK_PORT are already set above and will be read by app.py

echo Starting Flask app...
echo   FLASK_APP: %FLASK_APP%
echo   FLASK_ENV: %FLASK_ENV%
echo   FLASK_DEBUG: %FLASK_DEBUG%
echo   FLASK_PORT: %FLASK_PORT% (app.py will use this from environment)
echo.

REM Run the Flask app using python directly, as app.py has a __main__ block
python "%FLASK_APP_PATH%"

REM To use 'flask run' command instead (ensure FLASK_APP is set as above):
REM flask run --host=0.0.0.0 --port=%FLASK_PORT%

REM Deactivation of venv is usually not needed as the script/shell session ends.
REM If you were to continue in the same cmd window:
REM if exist "%VENV_PATH%\Scripts\deactivate.bat" (
REM   call "%VENV_PATH%\Scripts\deactivate.bat"
REM )
