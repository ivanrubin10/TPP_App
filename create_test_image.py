import numpy as np
import cv2
import os

# Create a test image folder if it doesn't exist
TEST_IMAGES_DIR = "./test_images"
if not os.path.exists(TEST_IMAGES_DIR):
    os.makedirs(TEST_IMAGES_DIR)

# Create a simple test image
def create_test_image():
    # Create a gray background
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # Add a colored rectangle for the "capot" (hood)
    cv2.rectangle(img, (150, 150), (490, 350), (70, 130, 180), -1)
    
    # Add some details to make it look more like a car hood
    cv2.line(img, (150, 250), (490, 250), (50, 50, 50), 2)
    cv2.line(img, (320, 150), (320, 350), (50, 50, 50), 1)
    
    # Add text
    cv2.putText(img, 'TEST IMAGE - SAMPLE HOOD', (120, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img, 'Camera Not Available', (180, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # Save the image
    test_image_path = os.path.join(TEST_IMAGES_DIR, 'test_capot.jpg')
    cv2.imwrite(test_image_path, img)
    print(f"Test image created at: {test_image_path}")
    
    # Create another variation
    img2 = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # Add a different colored rectangle for a different "capot" type
    cv2.rectangle(img2, (150, 150), (490, 350), (0, 100, 200), -1)
    
    # Add some different details
    cv2.line(img2, (150, 200), (490, 200), (50, 50, 50), 2)
    cv2.line(img2, (150, 300), (490, 300), (50, 50, 50), 2)
    
    # Add text
    cv2.putText(img2, 'TEST IMAGE - ALTERNATE HOOD', (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(img2, 'Camera Not Available', (180, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    
    # Save the second image
    test_image_path2 = os.path.join(TEST_IMAGES_DIR, 'test_capot2.jpg')
    cv2.imwrite(test_image_path2, img2)
    print(f"Second test image created at: {test_image_path2}")

if __name__ == "__main__":
    create_test_image()
    print("Test images created successfully!") 