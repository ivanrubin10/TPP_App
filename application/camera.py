import base64
import cv2
import os

def capture_image():
    """Load and encode a test image from a specified path."""
    try:
        # Get the absolute path of the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Specify the path to your test image
        image_path = os.path.join(current_dir, 'test_image.jpg')
        
        print(f"Loading image from: {image_path}")
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"File does not exist at path: {image_path}")
            raise FileNotFoundError(f"Test image not found at {image_path}")
            
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"OpenCV failed to load image from {image_path}")
            raise ValueError(f"Failed to load image from {image_path}")
            
        # Encode image
        _, buffer = cv2.imencode('.jpg', image)
        if buffer is None:
            print("Failed to encode image to JPEG")
            raise ValueError("Failed to encode image")
            
        encoded = base64.b64encode(buffer).decode('utf-8')
        print(f"Image encoded successfully. Length: {len(encoded)}")
        
        return encoded
        
    except Exception as e:
        print(f"Error loading test image: {str(e)}")
        raise

    # Commented out camera code
    """
    cap = None
    try:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            raise Exception("Could not open camera")

        # Capture frame
        ret, frame = cap.read()

        # Check if frame captured successfully
        if not ret:
            raise Exception("Failed to capture image")
        
        # Encode image
        _, buffer = cv2.imencode('.jpg', frame)
        if buffer is None:
            raise Exception("Failed to encode image")
            
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        return encoded_image
        
    except Exception as e:
        print(f"Error capturing image: {e}")
        raise
    finally:
        # Always release the camera
        if cap is not None:
            cap.release()
    """
