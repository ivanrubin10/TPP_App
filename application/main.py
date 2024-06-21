from flask import Flask, jsonify
from camera import capture_image
from flask_cors import CORS
from tflite_detector import tflite_detect_image

app = Flask(__name__)
CORS(app)  # Apply CORS for all routes
@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  try:
    image = capture_image()
    model_path = 'detect.tflite'
    label_path = 'labelmap.txt'
    min_conf_threshold = 0.5
    with open(label_path, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    result_image, detected_objects = tflite_detect_image(model_path, image, labels, min_conf_threshold)

    return jsonify({'image': image, 'objects': detected_objects, 'result_image': result_image})
  except Exception as e:
    return jsonify({'error': str(e)}), 500  # Internal Server Error

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
