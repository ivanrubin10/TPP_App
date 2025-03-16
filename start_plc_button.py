import os
import subprocess
import sys

def start_plc_simulator():
    """
    Start the PLC simulator in button mode
    """
    print("Starting PLC simulator in button mode...")
    
    # Build the command
    cmd = [sys.executable, "plc.py", "--mode", "button"]
    
    # Start the process
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
            
    except KeyboardInterrupt:
        print("\nStopping PLC simulator...")
        process.terminate()
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    start_plc_simulator() 