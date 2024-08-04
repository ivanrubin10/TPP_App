import subprocess
import webbrowser
import time
from threading import Thread

# Path to your Flask application
FLASK_APP = "../application/main.py"
# URL to open in the browser (this should be the Flask server address)
URL = "http://127.0.0.1:5000"

def run_flask():
    subprocess.run(["python", FLASK_APP])

def open_browser():
    time.sleep(5)  # Give Flask some time to start
    webbrowser.open(URL)

if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Open the Vue front-end in the default browser
    open_browser()

    # Keep the main thread alive
    flask_thread.join()
