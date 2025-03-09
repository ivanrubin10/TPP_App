import cv2
import numpy as np
import base64
import time

def detect_gray_percentage(base64_image):
    """
    Detects the percentage of gray pixels in a base64 encoded image.
    Returns the percentage of gray pixels in the image.
    """
    try:
        start_time = time.time()
        
        # Decode base64 image - optimize by skipping prefix if present
        if isinstance(base64_image, str) and ',' in base64_image:
            base64_image = base64_image.split(',')[1]
            
        image_data = base64.b64decode(base64_image)
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image")
        
        # Convert to HSV - this is faster than processing in RGB
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define gray range in HSV - low saturation and medium-high value indicates gray
        lower_gray = np.array([0, 0, 50])
        upper_gray = np.array([180, 30, 220])
        
        # Create mask for gray pixels
        mask = cv2.inRange(hsv, lower_gray, upper_gray)
        
        # Calculate percentage of gray pixels
        total_pixels = mask.size
        gray_pixels = cv2.countNonZero(mask)
        gray_percentage = (gray_pixels / total_pixels) * 100
        
        end_time = time.time()
        print(f"Gray detection completed in {(end_time - start_time) * 1000:.2f}ms. Result: {gray_percentage:.2f}% gray (threshold: 60%)")
        
        return gray_percentage
    except Exception as e:
        print(f"Error in gray detection: {str(e)}")
        raise
