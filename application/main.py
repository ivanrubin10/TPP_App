from flask import Flask, jsonify
from camera import capture_image
from flask_cors import CORS
from tflite_detector import detect_objects

app = Flask(__name__)
CORS(app)  # Apply CORS for all routes
@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  try:
    #image = capture_image()
    image = '123'
    # dummy data
    detected_objects = [{'class': 'tres_agujeros', 'score': 0.9, 'box': [0.1, 0.2, 0.3, 0.4]}]
    return jsonify({'image': image, 'objects': detected_objects})
  except Exception as e:
    return jsonify({'error': str(e)}), 500  # Internal Server Error

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
