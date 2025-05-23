#!/bin/bash

# Start the Flask backend server
cd FlaskBackend
python3 app.py &
BACKEND_PID=$!
echo "Backend server started with PID: $BACKEND_PID"

# Go back to the root directory
cd ..

# Start the frontend server
npm run dev &
FRONTEND_PID=$!
echo "Frontend server started with PID: $FRONTEND_PID"

# Function to handle script termination
cleanup() {
  echo "Stopping servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit
}

# Register the cleanup function for script termination
trap cleanup SIGINT SIGTERM

# Keep the script running
echo "Both servers are running. Press Ctrl+C to stop."
wait