"""
Application configuration settings
"""

# Development mode flag
DEV_MODE = False

# Server settings
BACKEND_HOST = 'localhost'
BACKEND_PORT = 5000
FRONTEND_PORT = 8080

# Browser settings
DEFAULT_BROWSER = 'chromium-browser'

# Timing settings
BACKEND_STARTUP_WAIT = 5  # seconds
FRONTEND_STARTUP_WAIT = 3  # seconds

def get_backend_url():
    return f"http://{BACKEND_HOST}:{BACKEND_PORT}"

def get_frontend_url():
    return f"http://{BACKEND_HOST}:{FRONTEND_PORT}" 