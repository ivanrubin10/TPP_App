import os
from scripts.services.process_manager import ProcessManager

class BackendService:
    def __init__(self):
        self.process_manager = ProcessManager("Backend")
        
    def start(self):
        """Start the Flask backend server."""
        command = ['python', 'application/main.py']
        return self.process_manager.start(command, shell=False)
        
    def stop(self):
        """Stop the backend server."""
        self.process_manager.stop()
        
    def wait(self):
        """Wait for the backend server to complete."""
        return self.process_manager.wait() 