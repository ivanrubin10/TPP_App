from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  image = capture_image()
  detected_objects = detect_objects(image)
  return jsonify({'image': image_to_base64(image), 'objects': detected_objects})

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)