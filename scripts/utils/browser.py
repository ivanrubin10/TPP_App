import subprocess
import webbrowser

def open_url(url: str, browser_command: str = 'chromium-browser'):
    """
    Open a URL in the browser.
    
    Args:
        url: The URL to open
        browser_command: The browser command to use (default: chromium-browser)
    """
    try:
        # First try using the specified browser command
        subprocess.Popen(
            [browser_command, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except:
        try:
            # Fall back to Python's webbrowser module
            webbrowser.open(url)
        except:
            print(f"Note: Could not open browser automatically. Please open {url} manually.") 