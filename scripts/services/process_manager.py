import subprocess
import threading
from typing import Optional, Callable

class ProcessManager:
    def __init__(self, name: str, on_output: Optional[Callable[[str], None]] = None):
        self.name = name
        self.process: Optional[subprocess.Popen] = None
        self.on_output = on_output or (lambda x: print(f"[{self.name}] {x.strip()}"))
        self.output_thread: Optional[threading.Thread] = None

    def _handle_output(self):
        """Handle process output in a separate thread."""
        if not self.process or not self.process.stdout:
            return
        
        for line in self.process.stdout:
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            self.on_output(line)

    def start(self, command, shell=True, **kwargs):
        """Start the process with the given command."""
        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=shell,
                bufsize=1,
                **kwargs
            )
            
            # Start output handling thread
            self.output_thread = threading.Thread(
                target=self._handle_output,
                daemon=True
            )
            self.output_thread.start()
            
            return self.process
            
        except Exception as e:
            self.on_output(f"Error starting process: {str(e)}")
            raise

    def stop(self):
        """Stop the process if it's running."""
        if self.process:
            self.process.terminate()
            self.process = None

    def wait(self):
        """Wait for the process to complete."""
        if self.process:
            return self.process.wait()
        return None 