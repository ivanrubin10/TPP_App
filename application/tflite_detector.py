import cv2
import numpy as np
import base64
from tensorflow.lite.python.interpreter import Interpreter
import traceback

def load_tflite_model(model_path):
    """
    Loads a TFLite model and returns the interpreter.
    This function is separated to allow for model caching.
    
    Parameters:
    - model_path: Path to the TFLite model file.
    
    Returns:
    - interpreter: The loaded TFLite interpreter.
    """
    try:
        print(f"Loading TFLite model from: {model_path}")
        interpreter = Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        print("Model loaded successfully")
        return interpreter
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        raise

def tflite_detect_image(model_path_or_interpreter, base64_image, labels, min_conf=0.5):
    """
    Runs TFLite model on the given base64 encoded image and returns the image with detection results encoded as base64,
    along with a list of detected objects.

    Parameters:
    - model_path_or_interpreter: Path to the TFLite model file or a pre-loaded interpreter.
    - base64_image: The input image as a base64 encoded string.
    - labels: List of labels corresponding to the model's classes.
    - min_conf: Minimum confidence threshold for displaying detected objects.

    Returns:
    - encoded_image: The resulting image with detection results as a base64 encoded string.
    - detected_objects: A list of dictionaries containing detected objects.
    """
    try:
        print("Starting TFLite detection...")
        
        # Decode the base64 image
        try:
            print("Decoding base64 image...")
            image_data = base64.b64decode(base64_image)
            np_arr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image")
            print(f"Image decoded successfully. Shape: {image.shape}")
        except Exception as e:
            print(f"Error decoding image: {str(e)}")
            raise

        # Load the TensorFlow Lite model into memory if not already loaded
        if isinstance(model_path_or_interpreter, str):
            try:
                interpreter = load_tflite_model(model_path_or_interpreter)
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                raise
        else:
            interpreter = model_path_or_interpreter

        # Get model details
        try:
            print("Getting model details...")
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            height = input_details[0]['shape'][1]
            width = input_details[0]['shape'][2]
            print(f"Model input dimensions: {width}x{height}")
        except Exception as e:
            print(f"Error getting model details: {str(e)}")
            raise

        float_input = (input_details[0]['dtype'] == np.float32)
        input_mean = 127.5
        input_std = 127.5

        # Process image
        try:
            print("Processing image...")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            imH, imW, _ = image.shape
            image_resized = cv2.resize(image_rgb, (width, height))
            input_data = np.expand_dims(image_resized, axis=0)

            # Normalize pixel values if using a floating model
            if float_input:
                input_data = (np.float32(input_data) - input_mean) / input_std
            print("Image processed successfully")
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            raise

        # Perform detection
        try:
            print("Running inference...")
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            # Retrieve detection results
            boxes = interpreter.get_tensor(output_details[1]['index'])[0]
            classes = interpreter.get_tensor(output_details[3]['index'])[0]
            scores = interpreter.get_tensor(output_details[0]['index'])[0]
            print(f"Inference completed. Found {len(scores)} potential detections")
        except Exception as e:
            print(f"Error during inference: {str(e)}")
            raise

        detected_objects = []

        # Process detections
        try:
            print("Processing detections...")
            for i in range(len(scores)):
                if ((scores[i] > min_conf) and (scores[i] <= 1.0)):
                    ymin = int(max(1, (boxes[i][0] * imH)))
                    xmin = int(max(1, (boxes[i][1] * imW)))
                    ymax = int(min(imH, (boxes[i][2] * imH)))
                    xmax = int(min(imW, (boxes[i][3] * imW)))

                    cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

                    object_name = labels[int(classes[i])]
                    label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    label_ymin = max(ymin, labelSize[1] + 10)
                    cv2.rectangle(image, (xmin, label_ymin - labelSize[1] - 10),
                                (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
                    cv2.putText(image, label, (xmin, label_ymin - 7),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

                    detected_objects.append({
                        'class': object_name,
                        'score': float(scores[i]),
                        'box': [float(boxes[i][1]), float(boxes[i][0]),
                               float(boxes[i][3]), float(boxes[i][2])]
                    })
            print(f"Processed {len(detected_objects)} objects above confidence threshold")
        except Exception as e:
            print(f"Error processing detections: {str(e)}")
            raise

        # Encode result image
        try:
            print("Encoding result image...")
            _, buffer = cv2.imencode('.jpg', image)
            if buffer is None:
                raise ValueError("Failed to encode result image")
            encoded_image = base64.b64encode(buffer).decode('utf-8')
            print("Result image encoded successfully")
        except Exception as e:
            print(f"Error encoding result image: {str(e)}")
            raise

        print("TFLite detection completed successfully")
        return encoded_image, detected_objects

    except Exception as e:
        print(f"Error in TFLite detection: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        raise