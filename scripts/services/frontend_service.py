import os
from scripts.services.process_manager import ProcessManager

class FrontendService:
    def __init__(self):
        self.process_manager = ProcessManager("Frontend")
        self.original_dir = os.getcwd()
        
    def start(self, dev_mode=False):
        """Start the frontend service."""
        try:
            # Change to frontend directory
            os.chdir('application-ui')
            
            if dev_mode:
                # Development mode
                return self.process_manager.start(
                    'npm run dev',
                    env=dict(os.environ, PATH=os.environ['PATH'])
                )
            else:
                # Production mode
                # Build first
                build_result = self.process_manager.start(
                    'npm run build',
                    env=dict(os.environ, PATH=os.environ['PATH'])
                )
                
                if build_result.wait() != 0:
                    raise Exception("Frontend build failed")
                
                # Then serve the built files
                return self.process_manager.start(
                    'python -m http.server 8080 --bind 0.0.0.0 --directory dist'
                )
                
        finally:
            # Always return to original directory
            os.chdir(self.original_dir)
            
    def stop(self):
        """Stop the frontend service."""
        self.process_manager.stop()
        
    def wait(self):
        """Wait for the frontend service to complete."""
        return self.process_manager.wait() 