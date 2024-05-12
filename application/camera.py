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

  return frame

def image_to_base64(image):
  # Encode image to base64 string (assuming RGB format)
  _, buffer = cv2.imencode('.jpg', image)
  return base64.b64encode(buffer).decode('utf-8')
