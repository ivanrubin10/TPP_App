import subprocess
import os
import time
import platform

def start_backend():
    print("Starting Flask backend...")
    backend_process = subprocess.Popen(
        ['python', 'application/main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    # Start a thread to read and print the output
    def print_output():
        for line in backend_process.stdout:
            print(f"[Backend] {line.strip()}")
    
    import threading
    threading.Thread(target=print_output, daemon=True).start()
    return backend_process

def start_frontend(dev_mode=True):
    # Store the original working directory
    original_dir = os.getcwd()
    
    try:
        # Change to the frontend directory using absolute path
        frontend_dir = os.path.join(original_dir, 'application-ui')
        os.chdir(frontend_dir)
        
        if dev_mode:
            print("Starting Vue.js frontend (development mode)...")
            frontend_process = subprocess.Popen(
                'npm run dev',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
        else:
            print("Serving Vue.js frontend (production mode)...")
            print("Building frontend...")
            # Build the frontend
            build_process = subprocess.run(
                'npm run build',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            if build_process.returncode != 0:
                print("Error building frontend:")
                print(build_process.stdout)
                raise Exception("Frontend build failed")
            
            print("Starting HTTP server...")
            # Start HTTP server on 0.0.0.0 to allow external access
            frontend_process = subprocess.Popen(
                'python -m http.server 8080 --bind 0.0.0.0 --directory dist',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
        
        # Start a thread to read and print the output
        def print_output():
            for line in frontend_process.stdout:
                print(f"[Frontend] {line.strip()}")
        
        import threading
        threading.Thread(target=print_output, daemon=True).start()
        
        return frontend_process
        
    finally:
        # Always return to the original directory
        os.chdir(original_dir)

def main():
    dev_mode = False  # Change this to False for production (using built files)

    # Get the machine's IP address
    import socket
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    print("Starting application...")
    
    backend_process = start_backend()
    print("Backend started, waiting for initialization...")
    time.sleep(5)  # Wait for the backend to start

    print("Starting frontend...")
    frontend_process = start_frontend(dev_mode)
    print("Frontend started, waiting for initialization...")
    time.sleep(3)  # Wait for frontend to start

    # Print access instructions
    print("\n" + "="*50)
    print(f"Application is running!")
    print(f"You can access it at: http://{ip_address}:8080")
    print("="*50 + "\n")

    try:
        # Keep the script running while both processes are active
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down processes...")
        backend_process.terminate()
        frontend_process.terminate()
        print("Application stopped.")

if __name__ == '__main__':
    main()
