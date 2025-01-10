import time
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
from dataclasses import dataclass


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

@dataclass
class LastSentMessage:
    terminal: bytes = None
    sender: bytes = None
    serial: bytes = None

last_sent_msg = LastSentMessage()

config = {
    "min_conf_threshold": 0.7,
    "connection_type": "PLC",  # Can be "PLC" or "GALC"
    "plc_host": "127.0.0.1",  # Default IP as a string
    "plc_port": 12345,        # Default port as a number
    "galc_host": "127.0.0.1", # Default GALC IP
    "galc_port": 54321        # Default GALC port
}

client_socket = None
client_thread = None

is_connected = False
client_socket = None
galc_connection = None
plc_connection = None

message_processing = False
# Added GALC response handling and connection logic
def handle_galc_response(conn):
    global message_processing, is_connected, galc_connection
    message_processing = False
    while True:
        socketio.emit('connection_status', {'status': True if is_connected else False})
        socketio.emit('connection_type', {'type': config['connection_type']})
        try:
            # Receive the 45-byte GALC message
            data = conn.recv(45)
            if len(data) != 45:
                print(f"Invalid GALC message length: {len(data)}. Closing connection.")
                break

            print(f"Received GALC message: Receiver: {data[0:6].decode()}, "
                  f"Sender: {data[6:12].decode()}, Serial: {data[12:16].decode()}, "
                  f"Trigger: {data[44]:02d}")

            # Extract and handle the last two bytes
            last_two_bytes = data[43:45]
            trigger_value = int.from_bytes(last_two_bytes, "big")  # Convert to integer
            trigger_str = f"{trigger_value:02d}"  # Ensure it is a 2-digit string


            if trigger_str in ["01", "05", "08"] and message_processing == False:
                print(f"Triggering Vue.js handler with value: {trigger_str}")
                socketio.emit('handle_message', {'message': trigger_str})  # Notify Vue.js frontend with defined message

            # Send a 26-byte response
            response = bytearray(26)
            response[:6] = data[6:12]  # Sender to receiver
            response[6:12] = data[0:6]  # Receiver to sender
            response[12:16] = data[12:16]  # Serial number
            response[25] = 1 if message_processing else 0  # Stop or keep-alive flag
            conn.sendall(response)
            print(f"Sent GALC response: Receiver: {response[0:6].decode()}, "
                  f"Sender: {response[6:12].decode()}, Serial: {response[12:16].decode()}, "
                  f"Status: {response[25]}")
            
            message_processing = True

        except Exception as e:
            print(f"Error handling GALC message: {e}")
            break
    conn.close()
    is_connected = False  # Update connection status
    galc_connection = None  # Reset GALC connection

def connect_to_galc():
    global client_socket, is_connected, galc_connection

    if galc_connection is not None:
        print("Already connected to GALC. Ignoring new connection attempt.")
        return
    host = config["galc_host"]
    port = config["galc_port"]

    try:
        conn = socket.create_connection((host, port))
        client_socket = conn
        galc_connection = conn
        is_connected = True  # Update connection status
        threading.Thread(target=handle_galc_response, args=(conn,), daemon=True).start()
    except Exception as e:
        print(f"GALC connection error: {e}")

def handle_plc_response(conn):
    global plc_connection
    while True:
        socketio.emit('connection_status', {'status': True if is_connected else False})
        socketio.emit('connection_type', {'type': config['connection_type']})
        try:
            # Receive data from the PLC
            data = conn.recv(1024)
            if not data:
                print("No data received from PLC, closing connection.")
                break

            print(f"Received PLC data: {data.decode(errors='replace')}")

            # Process PLC data and emit events as necessary
            message = data.decode()  # Example decoding
            socketio.emit('plc_message', {'message': message})  # Notify frontend
            time.wait(1)
            # Send a response back to the PLC
            response = b"OK" if "GOOD" in message else b"NG"
            conn.sendall(response)
            print(f"Sent PLC response: {response.decode()}")
        except Exception as e:
            print(f"Error handling PLC message: {e}")
            break
    conn.close()
    plc_connection = None  # Reset PLC connection

def connect_to_plc():
    global client_socket, is_connected, plc_connection

    if plc_connection is not None:
        print("Already connected to PLC. Ignoring new connection attempt.")
        return
    

    host = config["plc_host"]
    port = config["plc_port"]

    try:
        conn = socket.create_connection((host, port))
        client_socket = conn
        plc_connection = conn
        is_connected = True  # Update connection status
        threading.Thread(target=handle_plc_response, args=(conn,), daemon=True).start()
    except Exception as e:
        print(f"PLC connection error: {e}")

def retry_connection():
    print("Retrying connection...")
    if config['connection_type'] == "GALC":
        connect_to_galc()
    else:
        connect_to_plc()
# Start the appropriate connection based on connection type
@socketio.on('connect')
def handle_connect():
    global is_connected
    client_ip = request.remote_addr
    print(f"Client connected from IP: {client_ip}")

    # Check if already connected
    if is_connected:
        print("Already connected. Ignoring new connection attempt.")
        return

    is_connected = True  # Update connection status
    socketio.emit('connection_type', {'type': config['connection_type']})  # Send connection type on connect
    if config['connection_type'] == "GALC":
        connect_to_galc()
    else:
        connect_to_plc()

@socketio.on('disconnect')
def handle_disconnect():
    global is_connected
    is_connected = False  # Update connection status
    socketio.emit('connection_status', {'status': False})
    socketio.emit('connection_type', {'type': config['connection_type']})
    print('Client disconnected')

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({'status': f'connected to {config["connection_type"]}'}), 200

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/retry-connection', methods=['POST'])
def handle_retry_connection():
    retry_connection()
    return jsonify({'message': 'Retrying connection...'}), 200

@app.route('/capture-image', methods=['GET'])
def capture_and_detect():
  global config, capturing
  
  capturing = True
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
        car_log = db.session.get(CarLog, data['id'])
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
        if 'connection_type' in data:
            config['connection_type'] = str(data['connection_type'])
        if 'plc_host' in data:
            config['plc_host'] = str(data['plc_host'])
        if 'plc_port' in data:
            try:
                config['plc_port'] = int(data['plc_port'])
            except ValueError:
                return jsonify({"error": "plc_port must be an integer"}), 400
        if 'galc_host' in data:
            config['galc_host'] = str(data['galc_host'])
        if 'galc_port' in data:
            try:
                config['galc_port'] = int(data['galc_port'])
            except ValueError:
                return jsonify({"error": "galc_port must be an integer"}), 400

        
        return jsonify({"message": "Configuration updated successfully"}), 200



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
