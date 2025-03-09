import subprocess
import os
import time
import platform
import sys
import shutil

def get_available_memory_mb():
    """Get available memory in MB"""
    try:
        if platform.system() == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemAvailable' in line:
                        # Extract the value and convert to MB
                        return int(line.split()[1]) / 1024
        # Fallback for other platforms
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except:
        # If we can't determine memory, return a conservative estimate
        return 1024  # Assume 1GB

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

def start_frontend(dev_mode=True, skip_build=False):
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
            
            # Check if we're on a Raspberry Pi
            is_raspberry_pi = 'arm' in platform.machine().lower() or os.path.exists('/proc/device-tree/model') and 'raspberry pi' in open('/proc/device-tree/model').read().lower()
            
            # Check if dist directory already exists
            dist_exists = os.path.exists('dist') and os.path.isfile('dist/index.html')
            
            # Determine if we should build
            should_build = not skip_build
            
            if is_raspberry_pi:
                print("Detected Raspberry Pi environment.")
                
                # Check available memory
                available_memory = get_available_memory_mb()
                print(f"Available memory: {available_memory:.1f} MB")
                
                if available_memory < 600:  # Need at least 600MB for build
                    print("WARNING: Low memory detected on Raspberry Pi.")
                    if dist_exists:
                        print("Using existing build instead of creating a new one.")
                        should_build = False
                    else:
                        print("No existing build found. Will attempt to build but it may fail.")
                        # Set NODE_OPTIONS to limit memory usage even more aggressively
                        build_env = dict(os.environ, 
                                        PATH=os.environ['PATH'],
                                        NODE_OPTIONS="--max-old-space-size=384")
                else:
                    # Normal Raspberry Pi build with memory optimization
                    build_env = dict(os.environ, 
                                    PATH=os.environ['PATH'],
                                    NODE_OPTIONS="--max-old-space-size=512")
                
                # Increase timeout for Raspberry Pi
                build_timeout = 900  # 15 minutes
            else:
                build_env = dict(os.environ, PATH=os.environ['PATH'])
                build_timeout = 300  # 5 minutes
            
            # Build the frontend if needed
            if should_build:
                print("Building frontend (this may take several minutes on Raspberry Pi)...")
                try:
                    # Clean node_modules if on Raspberry Pi with low memory
                    if is_raspberry_pi and available_memory < 800 and os.path.exists('node_modules'):
                        print("Low memory environment detected. Cleaning node_modules to free up space...")
                        shutil.rmtree('node_modules', ignore_errors=True)
                        # Reinstall dependencies
                        print("Reinstalling dependencies...")
                        subprocess.run('npm install --no-optional', shell=True, check=True)
                    
                    # Build the frontend
                    build_result = subprocess.run(
                        'npm run build',
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        env=build_env,
                        timeout=build_timeout
                    )
                    
                    if build_result.returncode != 0:
                        print("Error during build:")
                        print(build_result.stdout)
                        if dist_exists:
                            print("Using existing build instead.")
                        else:
                            raise Exception("Frontend build failed and no previous build found.")
                except subprocess.TimeoutExpired:
                    print("Build process timed out. This might be due to limited resources on the device.")
                    if dist_exists:
                        print("Using existing build instead.")
                    else:
                        raise Exception("Frontend build timed out and no previous build found.")
                except Exception as e:
                    print(f"Build error: {str(e)}")
                    if dist_exists:
                        print("Using existing build instead.")
                    else:
                        raise Exception(f"Frontend build failed: {str(e)}")
            else:
                print("Skipping build process, using existing build.")
                
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

def open_browser(url):
    """Try to open the browser with multiple methods based on the platform"""
    print(f"Attempting to open browser at {url}")
    
    # Different commands to try based on platform
    if platform.system() == 'Linux':
        browsers = [
            ['chromium-browser', url],
            ['chromium', url],
            ['epiphany-browser', url],
            ['firefox', url],
            ['x-www-browser', url],
            ['xdg-open', url]
        ]
        
        for browser in browsers:
            try:
                subprocess.Popen(browser, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Opened browser using {browser[0]}")
                return True
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
    
    elif platform.system() == 'Darwin':  # macOS
        try:
            subprocess.Popen(['open', url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except:
            pass
    
    elif platform.system() == 'Windows':
        try:
            os.startfile(url)
            return True
        except:
            pass
    
    print("Could not open browser automatically. Please open the URL manually.")
    return False

def main():
    # Check for command line arguments
    dev_mode = '--dev' in sys.argv
    skip_build = '--skip-build' in sys.argv
    
    print(f"Starting application in {'development' if dev_mode else 'production'} mode")
    if skip_build:
        print("Build process will be skipped (--skip-build flag detected)")

    backend_process = start_backend()
    print("Waiting for backend to start...")
    time.sleep(5)  # Wait for the backend to start

    frontend_process = start_frontend(dev_mode, skip_build)
    print("Waiting for frontend to start...")
    time.sleep(3)  # Wait for frontend to start

    # Print access instructions
    local_ip = "localhost"
    try:
        # Try to get the local IP address for easier access from other devices
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        pass
    
    local_url = f"http://{local_ip}:8080"
    print("\n" + "="*50)
    print(f"Application is running!")
    print(f"You can access it at: {local_url}")
    print("="*50 + "\n")
    
    # Try to open the browser
    open_browser(local_url)

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
