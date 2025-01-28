import time
from scripts.services.backend_service import BackendService
from scripts.services.frontend_service import FrontendService
from scripts.utils.browser import open_url
from config.settings import (
    DEV_MODE,
    BACKEND_STARTUP_WAIT,
    FRONTEND_STARTUP_WAIT,
    DEFAULT_BROWSER,
    get_frontend_url
)

class Application:
    def __init__(self):
        self.backend = BackendService()
        self.frontend = FrontendService()
        
    def start(self):
        """Start the application."""
        try:
            # Start backend
            print("Starting backend service...")
            self.backend.start()
            time.sleep(BACKEND_STARTUP_WAIT)
            
            # Start frontend
            print("Starting frontend service...")
            self.frontend.start(dev_mode=DEV_MODE)
            time.sleep(FRONTEND_STARTUP_WAIT)
            
            # Print access information
            url = get_frontend_url()
            print("\n" + "="*50)
            print(f"Application is running!")
            print(f"You can access it at: {url}")
            print("="*50 + "\n")
            
            # Open browser
            open_url(url, DEFAULT_BROWSER)
            
            # Wait for processes
            self.wait()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"\nError: {str(e)}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop all services."""
        print("Stopping services...")
        self.frontend.stop()
        self.backend.stop()
        print("Application stopped.")
        
    def wait(self):
        """Wait for all services to complete."""
        try:
            self.backend.wait()
            self.frontend.wait()
        except KeyboardInterrupt:
            self.stop()

def main():
    app = Application()
    app.start()

if __name__ == '__main__':
    main() 