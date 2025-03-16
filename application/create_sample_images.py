import os
import cv2
import numpy as np

def create_sample_image(filename, text, color=(200, 200, 200)):
    """Create a sample image with text."""
    # Create a blank image (640x480)
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = color  # Set background color
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, text, (50, 240), font, 1, (0, 0, 0), 2)
    
    # Save the image
    cv2.imwrite(filename, img)
    print(f"Created sample image: {filename}")

def main():
    # Create sample_images directory if it doesn't exist
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample_images')
    os.makedirs(sample_dir, exist_ok=True)
    
    # Create sample images
    create_sample_image(
        os.path.join(sample_dir, 'no_capo.jpg'),
        "Sample Image: No Capo",
        color=(100, 100, 100)  # Dark gray
    )
    
    create_sample_image(
        os.path.join(sample_dir, 'capo_tipo_1.jpg'),
        "Sample Image: Capo Tipo 1",
        color=(200, 200, 200)  # Light gray (for Capo Tipo 1)
    )
    
    create_sample_image(
        os.path.join(sample_dir, 'capo_tipo_2.jpg'),
        "Sample Image: Capo Tipo 2",
        color=(180, 180, 180)  # Medium gray (for Capo Tipo 2)
    )
    
    create_sample_image(
        os.path.join(sample_dir, 'capo_tipo_3.jpg'),
        "Sample Image: Capo Tipo 3",
        color=(160, 160, 160)  # Another gray shade (for Capo Tipo 3)
    )
    
    print("All sample images created successfully.")

if __name__ == "__main__":
    main() 