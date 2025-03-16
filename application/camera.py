import base64
import cv2
import os
import numpy as np
import time
import platform
import uuid
import sys
import subprocess
from PIL import Image, ImageDraw, ImageFont

def list_available_cameras():
    """List all available camera devices to help with troubleshooting"""
    print("Checking available cameras...")
    available_cameras = []
    
    if platform.system() == 'Windows':
        # First try listing device info using DirectShow
        try:
            max_cameras = 5
            for i in range(max_cameras):
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    # Get camera info if possible
                    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    api = cap.get(cv2.CAP_PROP_BACKEND)
                    driver = cap.get(cv2.CAP_PROP_FOURCC)
                    
                    print(f"Found camera at index {i} - Resolution: {width}x{height}")
                    available_cameras.append({
                        'index': i,
                        'api': 'DirectShow',
                        'resolution': f"{width}x{height}"
                    })
                    
                cap.release()
        except Exception as e:
            print(f"Error enumerating DirectShow cameras: {e}")
            
    # If no cameras found, try other means
    if not available_cameras:
        print("No cameras found with primary method, trying alternative approaches...")
        try:
            if platform.system() == 'Windows':
                # Try to get information via PowerShell on Windows
                result = subprocess.run(
                    ["powershell", "Get-PnpDevice | Where-Object {$_.Class -eq 'Camera' -or $_.Class -eq 'Image'}"],
                    capture_output=True, text=True, check=False
                )
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Camera' in line or 'Webcam' in line or 'cam' in line.lower():
                            print(f"Found camera via PowerShell: {line.strip()}")
                    
        except Exception as e:
            print(f"Error checking cameras with alternative method: {e}")
    
    return available_cameras

def capture_image():
    """
    Simplified function to capture an image from the camera.
    Uses a basic approach with some error handling.
    Returns the image as a base64 encoded string.
    """
    print("Attempting to capture image from camera")
    
    # Create a basic capture object with default camera (usually index 0)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Failed to open camera with default index (0)")
        # Try with index 1 as fallback
        cap.release()
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("Failed to open camera with fallback index (1)")
            return create_placeholder_image("Camera not available - Could not open camera")
    
    # Wait for 1 second to allow camera to initialize and adjust
    time.sleep(1)
    
    # Capture a single frame
    ret, frame = cap.read()
    
    # Release the camera
    cap.release()
    
    # Check if we got a valid frame
    if not ret or frame is None or frame.size == 0:
        print("Failed to capture a valid frame")
        return create_placeholder_image("Camera not available - No valid frame captured")
    
    # Process and return the image
    return process_image(frame)

def process_image(frame):
    """Process the captured image and return as base64"""
    try:
        # Convert the frame to JPEG
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not success:
            print("Failed to encode image to JPEG")
            return create_placeholder_image("Failed to encode image")
        
        # Convert to base64
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print(f"Successfully encoded image, size: {len(image_base64) / 1024:.2f} KB")
        return image_base64
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return create_placeholder_image(f"Error: {str(e)}")

def create_placeholder_image(message="Camera not available"):
    """Create a placeholder image with error message when camera fails"""
    # Create a blank image with text
    width, height = 640, 480
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (50, 50, 50)  # Dark gray background
    
    # Add timestamp and border
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(img, timestamp, (width - 180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.rectangle(img, (10, 10), (width-10, height-10), (100, 100, 100), 2)
    
    # Put error message in the center
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(message, font, 0.8, 2)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    cv2.putText(img, message, (text_x, text_y), font, 0.8, (50, 50, 220), 2)
    
    # Add instructions
    instruction = "Please check camera connection"
    cv2.putText(img, instruction, (width//2 - 120, height - 30), font, 0.6, (200, 200, 200), 1)
    
    # Convert to base64
    success, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return image_base64