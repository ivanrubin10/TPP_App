# Running the TPP App on Raspberry Pi

This document provides instructions for setting up and running the TPP App on a Raspberry Pi.

## Prerequisites

Before running the application, make sure you have the following installed:

1. Python 3.7 or higher
2. Node.js and npm (Node.js 14 or higher recommended)
3. Required Python packages:
   - Flask
   - Flask-SocketIO
   - OpenCV (opencv-python)
   - TensorFlow Lite (tflite-runtime)
   - SQLAlchemy
   - marshmallow-sqlalchemy

## Installation

1. Clone the repository to your Raspberry Pi:
   ```
   git clone <repository-url>
   cd TPP\ App
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```
   cd application-ui
   npm install
   cd ..
   ```

## Running the Application

### Option 1: Using the start_app.py script (Recommended)

The `start_app.py` script has been optimized for Raspberry Pi and will automatically:
- Start the Flask backend
- Build the frontend (or use an existing build)
- Serve the frontend using a simple HTTP server
- Open a browser to the application

```
python start_app.py
```

### Command-line Options

- `--dev`: Run in development mode (not recommended for Raspberry Pi due to resource constraints)
- `--skip-build`: Skip the frontend build process and use an existing build (useful if you've already built the frontend)

Example:
```
python start_app.py --skip-build
```

### Option 2: Manual Startup

If you prefer to start the components manually:

1. Build the frontend (only needed once):
   ```
   cd application-ui
   NODE_OPTIONS=--max-old-space-size=512 npm run build
   cd ..
   ```

2. Start the backend:
   ```
   python application/main.py
   ```

3. Serve the frontend (in a separate terminal):
   ```
   cd application-ui
   python -m http.server 8080 --bind 0.0.0.0 --directory dist
   ```

4. Open a browser and navigate to `http://localhost:8080`

## Troubleshooting

### Memory Issues During Build

The Raspberry Pi has limited memory, which can cause problems during the frontend build process. If you encounter memory-related errors:

1. Try using the `--skip-build` option if you already have a built frontend:
   ```
   python start_app.py --skip-build
   ```

2. If you need to build the frontend, try freeing up memory:
   - Close other applications
   - Increase swap space temporarily
   - Build on a more powerful machine and copy the `dist` folder to your Raspberry Pi

### Browser Issues

If the browser doesn't open automatically:
1. Wait for the message "Application is running!"
2. Manually open a browser and navigate to the URL shown in the console (usually `http://localhost:8080`)

### Connection Issues

If you can't connect to the application from another device:
1. Make sure your Raspberry Pi and the other device are on the same network
2. Use the IP address shown in the console instead of `localhost`
3. Check if any firewall is blocking port 8080

## Performance Optimization

For better performance on Raspberry Pi:
1. Use a Raspberry Pi 4 with at least 2GB RAM if possible
2. Use a fast microSD card (Class 10 or better)
3. Consider overclocking your Raspberry Pi if you're comfortable doing so
4. Always use the `--skip-build` option after the first successful build

## Building on Another Machine

If your Raspberry Pi struggles with building the frontend, you can build it on another machine:

1. Clone the repository on a more powerful computer
2. Build the frontend:
   ```
   cd application-ui
   npm install
   npm run build
   ```
3. Copy the entire `dist` folder to the same location on your Raspberry Pi
4. Run the application with `--skip-build`:
   ```
   python start_app.py --skip-build
   ``` 