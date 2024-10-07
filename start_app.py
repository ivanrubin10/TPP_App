import subprocess
import os
import time
import webbrowser

def start_backend():
    print("Starting Flask backend...")
    backend_process = subprocess.Popen(['python', 'application/main.py'])
    return backend_process

def start_frontend(dev_mode=True):
    if dev_mode:
        print("Starting Vue.js frontend (development mode)...")
        os.chdir('application-ui')  # Ensure you're in the application-ui folder
        frontend_process = subprocess.Popen(['npm', 'run', 'dev'], shell=True)
    else:
        print("Serving Vue.js frontend (production mode)...")
        os.chdir('application-ui')
        subprocess.run(['npm', 'run', 'build'], shell=True)  # Ensure npm is found on Windows
        frontend_process = subprocess.Popen(['python', '-m', 'http.server', '--directory', 'dist', '8080'], shell=True)
    return frontend_process


def open_browser(dev_mode=True):
    if dev_mode:
        url = "http://localhost:5173"  # Default port for Vite in Vue.js dev mode
    else:
        url = "http://localhost:8080"  # Port for the production server

    print(f"Opening browser at {url}...")
    webbrowser.open(url)

def main():
    dev_mode = False  # Change this to False for production (using built files)

    backend_process = start_backend()
    time.sleep(5)  # Wait for the backend to start

    frontend_process = start_frontend(dev_mode)
    
    # Give the frontend some time to start before opening the browser
    time.sleep(3)  # Adjust this sleep time if necessary

    # Open the browser to the frontend URL
    open_browser(dev_mode)

    try:
        # Keep the script running while both processes are active
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("Shutting down processes...")
        backend_process.terminate()
        frontend_process.terminate()

if __name__ == '__main__':
    main()
