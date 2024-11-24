from flask import Flask, jsonify, request, send_from_directory
import socket
import threading
from flask_socketio import SocketIO, emit
from camera import capture_image
from flask_cors import CORS
from tflite_detector import tflite_detect_image
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field


app = Flask(__name__, static_folder='../application-ui', static_url_path='/')
CORS(app)  # Allow specific frontend

socketio = SocketIO(app, cors_allowed_origins="*")  # Allow SocketIO connections from the frontend

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
    date = db.Column(db.String(50), nullable=False)
    expected_part = db.Column(db.String(200), nullable=False)
    actual_part = db.Column(db.String(200), nullable=False)
    original_image_path = db.Column(db.String(200), nullable=False)
    result_image_path = db.Column(db.String(200), nullable=False)
    outcome = db.Column(db.String(200), nullable=False)

class CarLogSchema(SQLAlchemySchema):
    class Meta:
        model = CarLog
        load_instance = True

    id = auto_field()
    car_id = auto_field()
    date = auto_field()
    expected_part = auto_field()
    actual_part = auto_field()
    original_image_path = auto_field()
    result_image_path = auto_field()
    outcome = auto_field()

car_log_schema = CarLogSchema()
car_logs_schema = CarLogSchema(many=True)

# Initialize the database tables
with app.app_context():
    db.create_all()

config = {
    "min_conf_threshold": 0.7,
    "plc_host": "127.0.0.1",  # Default IP as a string
    "plc_port": 12345         # Default port as a number
}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


def start_client():
    host = '127.0.0.1'  # IP address of the PLC
    port = 12345             # Port number

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
client_thread = None
client_socket = None

def start_client(host, port):
    global client_socket, client_thread

    # Close any existing client socket
    if client_socket:
        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing previous socket: {e}")

    def client_logic():
        global client_socket
        try:
            # Create and connect a new client socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            print(f"Connected to PLC at {host}:{port}")
            
            # Keep the connection alive
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                message = data.decode()
                print(f"Received message: {message}")

                # Call handle_plc_message to emit the event
                handle_plc_message(message)

        except Exception as e:
            print(f"Client error: {e}")

    # Start the client in a new thread
    client_thread = threading.Thread(target=client_logic, daemon=True)
    client_thread.start()

def handle_plc_message(message):
    print("Message received from PLC:", message)
    # Emit a WebSocket event to notify the frontend
    socketio.emit('plc_message', {'message': message})

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({'status': 'connected to PLC'}), 200

@app.after_request
def start_background_task(response):
    global config
    if not hasattr(app, 'background_thread_started'):
        app.background_thread_started = True
        socketio.start_background_task(start_client(config['plc_host'], config['plc_port']))  # Use this instead of threading
    return response

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  global config
  try:
    print("Capturing image...")
    image = capture_image()
    print("Image captured!")
    # Try with application path first, fallback to current directory
    try:
        model_path = './application/detect.tflite'
        label_path = './application/labelmap.txt'
        with open(label_path, 'r') as f:
            labels = [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        model_path = './detect.tflite'
        label_path = './labelmap.txt'
        with open(label_path, 'r') as f:
            labels = [line.strip() for line in f.readlines()]

    print(config['min_conf_threshold'])
    result_image, detected_objects = tflite_detect_image(model_path, image, labels, config['min_conf_threshold'])
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
            car_log.date = data['date']
            car_log.expected_part = data['expected_part']
            car_log.actual_part = data['actual_part']
            car_log.original_image_path = data['original_image_path']
            car_log.result_image_path = data['result_image_path']
            car_log.outcome = data['outcome']
            db.session.commit()
            # Convert the updated car log object to a dictionary
            updated_log = {
                'id': car_log.id,
                'car_id': car_log.car_id,
                'date': car_log.date,
                'expected_part': car_log.expected_part,
                'actual_part': car_log.actual_part,
                'original_image_path': car_log.original_image_path,
                'result_image_path': car_log.result_image_path,
                'outcome': car_log.outcome,
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
            date=data['date'],
            expected_part=data['expected_part'],
            actual_part=data['actual_part'],
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
            'date': new_log.date,
            'expected_part': new_log.expected_part,
            'actual_part': new_log.actual_part,
            'original_image_path': new_log.original_image_path,
            'result_image_path': new_log.result_image_path,
            'outcome': new_log.outcome,
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

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        # Return the current configuration
        return jsonify(config)

    elif request.method == 'POST':
        # Update configuration with incoming data
        data = request.json
        if 'min_conf_threshold' in data:
            config['min_conf_threshold'] = float(data['min_conf_threshold'])
        if 'plc_host' in data:
            config['plc_host'] = str(data['plc_host'])
        if 'plc_port' in data:
            try:
                config['plc_port'] = int(data['plc_port'])
            except ValueError:
                return jsonify({"error": "plc_port must be an integer"}), 400

        # Restart the client with the updated configuration
        start_client(config['plc_host'], config['plc_port'])    
        
        return jsonify({"message": "Configuration updated successfully"}), 200



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
