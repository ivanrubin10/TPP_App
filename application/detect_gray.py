import cv2
import numpy as np
import base64

def detect_gray_percentage(base64_image):
    """
    Detects the percentage of gray pixels in a base64 encoded image.
    Returns the percentage of gray pixels in the image.
    """
    try:
        print("\n=== Starting Gray Percentage Detection ===")
        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        print(f"✓ Image decoded successfully")
        print(f"  - Shape: {image.shape}")
        print(f"  - Size: {image.size} pixels")
        
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        print("✓ Converted image to HSV color space")
        
        # Define gray range in HSV
        # Low saturation and medium-high value indicates gray
        lower_gray = np.array([0, 0, 50])
        upper_gray = np.array([180, 30, 220])
        print("✓ HSV ranges for gray detection:")
        print(f"  - Lower bound: H={lower_gray[0]}, S={lower_gray[1]}, V={lower_gray[2]}")
        print(f"  - Upper bound: H={upper_gray[0]}, S={upper_gray[1]}, V={upper_gray[2]}")
        
        # Create mask for gray pixels
        mask = cv2.inRange(hsv, lower_gray, upper_gray)
        print("✓ Created gray pixel mask")
        
        # Calculate percentage of gray pixels
        total_pixels = mask.size
        gray_pixels = cv2.countNonZero(mask)
        gray_percentage = (gray_pixels / total_pixels) * 100
        print("\n=== Gray Detection Results ===")
        print(f"• Total pixels: {total_pixels:,}")
        print(f"• Gray pixels: {gray_pixels:,}")
        print(f"• Gray percentage: {gray_percentage:.2f}%")
        print(f"• Status: {'SUFFICIENT' if gray_percentage >= 60 else 'INSUFFICIENT'} (threshold: 60%)")
        print("===============================\n")
        
        return gray_percentage
    except Exception as e:
        print("\n!!! Error in Gray Detection !!!")
        print(f"Error message: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        print("===============================\n")
        raise
