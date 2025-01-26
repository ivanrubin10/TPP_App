import subprocess
import os
import time

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
    # Store the original directory
    original_dir = os.getcwd()
    
    try:
        if dev_mode:
            print("Starting Vue.js frontend (development mode)...")
            os.chdir('application-ui')
            frontend_process = subprocess.Popen(
                'npm run dev',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                env=dict(os.environ, PATH=os.environ['PATH'])
            )
        else:
            print("Serving Vue.js frontend (production mode)...")
            os.chdir('application-ui')
            print("Building frontend...")
            # Build the frontend
            build_result = subprocess.run(
                'npm run build',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=dict(os.environ, PATH=os.environ['PATH'])
            )
            
            if build_result.returncode != 0:
                print("Error during build:")
                print(build_result.stdout)
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
    
    # Open the browser using chromium-browser
    try:
        subprocess.Popen(['chromium-browser', local_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        print("Note: Could not open browser automatically. Please open the URL manually.")

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
