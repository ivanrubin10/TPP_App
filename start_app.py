import subprocess
import os
import time
import webbrowser

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
    if dev_mode:
        print("Starting Vue.js frontend (development mode)...")
        os.chdir('application-ui')
        frontend_process = subprocess.Popen(
            ['npm', 'run', 'dev'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
    else:
        print("Serving Vue.js frontend (production mode)...")
        os.chdir('application-ui')
        # Build the frontend
        subprocess.run(
            ['npm', 'run', 'build'],
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        # Start HTTP server on 0.0.0.0 to allow external access
        frontend_process = subprocess.Popen(
            ['python', '-m', 'http.server', '8080', '--bind', '0.0.0.0', '--directory', 'dist'],
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

def main():
    dev_mode = False  # Change this to False for production (using built files)

    backend_process = start_backend()
    time.sleep(5)  # Wait for the backend to start

    frontend_process = start_frontend(dev_mode)
    time.sleep(3)  # Wait for frontend to start

    # Print access instructions
    local_url = "http://localhost:8080"
    print("\n" + "="*50)
    print(f"Application is running!")
    print(f"You can access it at: {local_url}")
    print("="*50 + "\n")
    
    # Open the browser
    webbrowser.open(local_url)

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
