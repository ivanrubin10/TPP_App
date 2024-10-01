from flask import Flask, jsonify, request, send_from_directory
from camera import capture_image
from flask_cors import CORS
from tflite_detector import tflite_detect_image
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field


app = Flask(__name__, static_folder='../application-ui/dist', static_url_path='/')
CORS(app)  # Apply CORS for all routes

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///car_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'

db = SQLAlchemy(app)
ma = Marshmallow(app)

# Define CarLog model
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.String(50), unique=True, nullable=False)
    car_info = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    original_image_path = db.Column(db.String(200), nullable=False)
    result_image_path = db.Column(db.String(200), nullable=False)
    outcome = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class CarLogSchema(SQLAlchemySchema):
    class Meta:
        model = CarLog
        load_instance = True

    id = auto_field()
    car_id = auto_field()
    car_info = auto_field()
    date = auto_field()
    original_image_path = auto_field()
    result_image_path = auto_field()
    outcome = auto_field()
    timestamp = auto_field()

car_log_schema = CarLogSchema()
car_logs_schema = CarLogSchema(many=True)

# Initialize the database tables
with app.app_context():
    db.create_all()

min_conf_threshold = 0.5  # Default value

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  global min_conf_threshold
  try:
    print("Capturing image...")
    image = capture_image()
    print("Image captured!")
    model_path = './dist/detect.tflite'
    label_path = './dist/labelmap.txt'
    with open(label_path, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    print(min_conf_threshold)
    result_image, detected_objects = tflite_detect_image(model_path, image, labels, min_conf_threshold)
    print("Objects detected!")
    return jsonify({'image': image, 'objects': detected_objects, 'result_image': result_image})
  except Exception as e:
    return jsonify({'error': str(e)}), 500  # Internal Server Error

@app.route('/check-car/<car_id>', methods=['GET'])
def check_car(car_id):
    car_log = CarLog.query.filter_by(car_id=car_id).first()
    if car_log:
        return jsonify({'exists': True, 'car_log': car_log_schema.dump(car_log)})
    else:
        return jsonify({'exists': False})

@app.route('/update-item', methods=['PUT'])
def update_item():
    try:
        data = request.get_json()
        car_log = CarLog.query.get(data['id'])
        if car_log:
            car_log.car_id = data['car_id']
            car_log.car_info = data['car_info']
            car_log.date = data['date']
            car_log.original_image_path = data['original_image_path']
            car_log.result_image_path = data['result_image_path']
            car_log.outcome = data['outcome']
            db.session.commit()
            # Convert the updated car log object to a dictionary
            updated_log = {
                'id': car_log.id,
                'car_id': car_log.car_id,
                'car_info': car_log.car_info,
                'date': car_log.date,
                'original_image_path': car_log.original_image_path,
                'result_image_path': car_log.result_image_path,
                'outcome': car_log.outcome,
                'timestamp': car_log.timestamp
            }
            return jsonify(updated_log)
        else:
            return jsonify({'error': 'Car log not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/log', methods=['POST'])
def add_log():
    try:
        data = request.get_json()
        new_log = CarLog(
            car_id=data['car_id'],
            car_info=data['car_info'],
            date=data['date'],
            original_image_path=data['original_image_path'],
            result_image_path=data['result_image_path'],
            outcome=data['outcome']
        )
        db.session.add(new_log)
        db.session.commit()
        
        # Convert the new log to a dictionary for JSON serialization
        log_dict = {
            'id': new_log.id,
            'car_id': new_log.car_id,
            'car_info': new_log.car_info,
            'date': new_log.date,
            'original_image_path': new_log.original_image_path,
            'result_image_path': new_log.result_image_path,
            'outcome': new_log.outcome,
            'timestamp': new_log.timestamp
        }
        
        return jsonify(log_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    all_logs = CarLog.query.all()
    result = car_logs_schema.dump(all_logs)
    return jsonify(result)

#   const saveConfig = async (config) => {
#     try {
#       const response = await axios.post(`${baseUrl}/config`, config)
#       return response.data
#     } catch (error) {
#       console.error('Error saving config:', error)
#       throw error
#     }
#   }
# this is how its called from the front end

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({'min_conf_threshold': min_conf_threshold})

@app.route('/config', methods=['POST'])
def save_config():
    global min_conf_threshold
    try:
        data = request.get_json()
        min_conf_threshold = data.get('min_conf_threshold', min_conf_threshold)
        return jsonify({'message': 'Config saved successfully', 'min_conf_threshold': min_conf_threshold})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
