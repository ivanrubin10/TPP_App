import cv2
import numpy as np
import base64
from tensorflow.lite.python.interpreter import Interpreter
import time

def load_tflite_model(model_path):
    """
    Load a TFLite model and allocate tensors.
    
    Parameters:
    - model_path: Path to the TFLite model file.
    
    Returns:
    - interpreter: TFLite interpreter with allocated tensors.
    """
    print(f"Loading TFLite model from {model_path}")
    start_time = time.time()
    interpreter = Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    print(f"Model loaded and tensors allocated in {time.time() - start_time:.2f} seconds")
    return interpreter

def tflite_detect_image(interpreter, base64_image, labels, min_conf=0.5, early_exit=False):
    """
    Runs TFLite model on the given base64 encoded image and returns the image with detection results encoded as base64,
    along with a list of detected objects.

    Parameters:
    - interpreter: TFLite interpreter with allocated tensors.
    - base64_image: The input image as a base64 encoded string.
    - labels: List of labels corresponding to the model's classes.
    - min_conf: Minimum confidence threshold for displaying detected objects.
    - early_exit: If True, will exit early after checking a few detections (for high gray % images)

    Returns:
    - encoded_image: The resulting image with detection results as a base64 encoded string.
    - detected_objects: A list of dictionaries containing detected objects.
    """
    start_time = time.time()
    
    # Decode the base64 image
    try:
        # Skip the data:image/jpeg;base64, prefix if present
        if isinstance(base64_image, str) and ',' in base64_image:
            base64_image = base64_image.split(',')[1]
            
        image_data = base64.b64decode(base64_image)
        np_arr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
    except Exception as e:
        print(f"Error decoding image: {str(e)}")
        raise

    decode_time = time.time()
    print(f"Image decode time: {(decode_time - start_time) * 1000:.2f}ms")
    
    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]
    
    # Store original image dimensions
    imH, imW = image.shape[:2]
    
    # Prepare input data - optimize by doing operations in-place when possible
    # Convert to RGB and resize in one step if possible
    image_resized = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_resized, (width, height))
    
    # Check if model uses floating point input
    float_input = (input_details[0]['dtype'] == np.float32)
    
    # Prepare input tensor
    if float_input:
        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        input_data = np.expand_dims(image_resized, axis=0).astype(np.float32)
        input_data = (input_data - 127.5) / 127.5
    else:
        # For quantized models
        input_data = np.expand_dims(image_resized, axis=0)
    
    preprocess_time = time.time()
    print(f"Preprocessing time: {(preprocess_time - decode_time) * 1000:.2f}ms")
    
    # Perform the actual detection
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    inference_time = time.time()
    print(f"Inference time: {(inference_time - preprocess_time) * 1000:.2f}ms")
    
    # Retrieve detection results
    boxes = interpreter.get_tensor(output_details[1]['index'])[0]
    classes = interpreter.get_tensor(output_details[3]['index'])[0]
    scores = interpreter.get_tensor(output_details[0]['index'])[0]
    
    # Process results
    detected_objects = []
    
    # Pre-calculate scaling factors
    y_scale, x_scale = imH, imW
    
    # Only process detections above threshold
    valid_indices = np.where(scores > min_conf)[0]
    
    # For early exit (high gray % images), just check if there are any valid detections
    # and return quickly without drawing bounding boxes
    if early_exit:
        if len(valid_indices) == 0:
            print("Early exit: No objects detected above threshold")
            # Return original image and empty objects list
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
            encoded_image = base64.b64encode(buffer).decode('utf-8')
            
            end_time = time.time()
            print(f"Early exit total time: {(end_time - start_time) * 1000:.2f}ms")
            return encoded_image, []
    
    for i in valid_indices:
        if scores[i] <= 1.0:  # Ensure score is valid
            # Get bounding box coordinates
            ymin = int(max(1, (boxes[i][0] * y_scale)))
            xmin = int(max(1, (boxes[i][1] * x_scale)))
            ymax = int(min(imH, (boxes[i][2] * y_scale)))
            xmax = int(min(imW, (boxes[i][3] * x_scale)))
            
            # Draw bounding box
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)
            
            # Get class name and prepare label
            class_id = int(classes[i])
            object_name = labels[class_id]
            confidence = int(scores[i] * 100)
            label = f'{object_name}: {confidence}%'
            
            # Draw label background and text
            labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            label_ymin = max(ymin, labelSize[1] + 10)
            cv2.rectangle(image, (xmin, label_ymin - labelSize[1] - 10), 
                         (xmin + labelSize[0], label_ymin + baseLine - 10), 
                         (255, 255, 255), cv2.FILLED)
            cv2.putText(image, label, (xmin, label_ymin - 7), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            
            # Add to detected objects list
            detected_objects.append({
                'class': object_name,
                'score': float(scores[i]),
                'box': [float(boxes[i][1]), float(boxes[i][0]), float(boxes[i][3]), float(boxes[i][2])]
            })
    
    postprocess_time = time.time()
    print(f"Postprocessing time: {(postprocess_time - inference_time) * 1000:.2f}ms")
    
    # Encode result image - use higher JPEG quality for better results
    _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    
    encode_time = time.time()
    print(f"Image encoding time: {(encode_time - postprocess_time) * 1000:.2f}ms")
    print(f"Total processing time: {(encode_time - start_time) * 1000:.2f}ms")
    
    return encoded_image, detected_objects