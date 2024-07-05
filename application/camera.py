import base64
import cv2

def capture_image():
  # Initialize camera
  cap = cv2.VideoCapture(0)

  # Capture frame
  ret, frame = cap.read()

  # Release camera
  cap.release()

  # Check if frame captured successfully
  if not ret:
    raise Exception("Failed to capture image")
  
  encoded_image = base64.b64encode(cv2.imencode('.jpg', frame)[1]).decode('utf-8')
    
  return encoded_image
