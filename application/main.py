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
    "connection_type": "PLC", # Can be "PLC" or "GALC"
    "plc_host": "127.0.0.1",  # Default IP as a string
    "plc_port": 12345,        # Default port as a number
    "galc_host": "127.0.0.1", # Default GALC IP
    "galc_port": 54321        # Default GALC port
}

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Start connection based on config type
    if config['connection_type'] == "PLC":
        start_client(config['plc_host'], config['plc_port'])
    else:
        start_client(config['galc_host'], config['galc_port'])

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

client_thread = None
client_socket = None

first_message = True  # Initialize first_message as a global variable

def start_client(host, port):
    global client_socket, client_thread  # Declare client_socket and client_thread as global

    # Close any existing client socket
    if client_socket:
        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing previous socket: {e}")

    def client_logic():
        global client_socket, first_message  # Include first_message in global declaration
        try:
            # Create and connect a new client socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))
            print(f"Connected to {config['connection_type']} at {host}:{port}")
            socketio.emit(f'{config["connection_type"].lower()}_connect')
            
            # Keep the connection alive
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                if config['connection_type'] == "GALC":
                    # Extract fields from 45 byte GALC message
                    line = data[26:27].decode()  # Byte 27
                    tracking_point = data[27:29].decode()  # Bytes 28-29
                    bc_sequence = data[29:32].decode()  # Bytes 30-32
                    last_byte = data[44:45]  # Last byte (random 1,5,8)
                    
                    print(f"Line: {line}")
                    print(f"Tracking Point: {tracking_point}")
                    print(f"BC Sequence: {bc_sequence}")
                    print(f"Last byte value: {int.from_bytes(last_byte, 'big')}")

                    # Construct 26 byte response
                    response = bytearray(26)
                    # Set terminal name from GALC message sender name (bytes 7-12)
                    response[0:6] = data[6:12]
                    # Set sender name from GALC message terminal name (bytes 1-6)
                    response[6:12] = data[0:6]
                    # Set serial number (bytes 13-16)
                    response[12:16] = data[12:16]
                    # Set bytes 17-25 to 0
                    response[16:25] = bytes([0] * 9)
                    # Set last byte to 0 if first message, 1 otherwise
                    response[25] = 0 if first_message else 1

                    if first_message:
                        # Use last two bytes for message value
                        last_two_bytes = data[43:45]
                        last_two_bytes_val = int.from_bytes(last_two_bytes, 'big')
                        message = f"{last_two_bytes_val:02d}" # Format as 2 digits
                        print(f"Received message value: {message}")
                        message_handler.handle_message(message)  # Use message_handler instance
                        first_message = False
                    
                    client_socket.sendall(response)
                else:
                    message = data.decode()
                    print(f"Received message: {message}")
                    message_handler.handle_message(message)  # Use message_handler instance

        except Exception as e:
            print(f"Client error: {e}")
            socketio.emit(f'{config["connection_type"].lower()}_disconnect')
            

    # Start the client in a new thread
    client_thread = threading.Thread(target=client_logic, daemon=True)
    client_thread.start()

class MessageHandler:
    def __init__(self):
        self.message_received = False
        self.lock = threading.Lock()  # Add thread lock

    def handle_message(self, message):
        with self.lock:  # Use lock to ensure thread safety
            if not self.message_received:
                print(f"Message received from {config['connection_type']}:", message)
                # Emit a WebSocket event to notify the frontend
                socketio.emit(f'{config["connection_type"].lower()}_message', {'message': message})
                self.message_received = True

# Create an instance of the MessageHandler class
message_handler = MessageHandler()

# Remove redundant handlers since we're using the message_handler instance directly
@socketio.on('plc_message')
@socketio.on('galc_message')
def handle_message(message):
    pass  # No longer needed since we use message_handler directly

@socketio.on('plc_response')
@socketio.on('galc_response')
def handle_response(message):
    print(f"{config['connection_type']} response emitted: {message.get('message')}")
    
    if config['connection_type'] == "PLC":
        # Create bytes directly for OK ("OK") and NG ("NG")
        msg_OK = bytes([0b01001111, 0b01001011])  # "OK" in ASCII
        msg_NG = bytes([0b01001110, 0b01000111])  # "NG" in ASCII
        
        if message.get('message') == "GOOD":
            try:
                client_socket.sendall(msg_OK)
            except Exception as e:
                print(f"Error sending response to PLC: {e}")
        elif message.get('message') == "NOGOOD":
            try:
                client_socket.sendall(msg_NG)
            except Exception as e:
                print(f"Error sending response to PLC: {e}")
                
    else:  # GALC response
        response = bytearray(45)  # Create 45 byte message
        
        # Ensure last_sent_msg has valid data before copying
        if last_sent_msg.terminal and last_sent_msg.sender and last_sent_msg.serial:
            response[0:6] = last_sent_msg.terminal
            response[6:12] = last_sent_msg.sender
            response[12:16] = last_sent_msg.serial
        else:
            print("Warning: last_sent_msg does not contain valid data.")
            response[0:16] = bytes([0] * 16)  # Fill with zeros if data is invalid
        
        # Set bytes 17-25 to 0
        response[16:25] = bytes([0] * 9)
        
        # Set response status based on first_message variable
        response[25] = 0 if first_message else 1  # 0 if first_message is true, 1 otherwise
            
        try:
            client_socket.sendall(response)
        except Exception as e:
            print(f"Error sending response to GALC: {e}")

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({'status': f'connected to {config["connection_type"]}'}), 200

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

        # Restart the client with the updated configuration
        if config['connection_type'] == "PLC":
            start_client(config['plc_host'], config['plc_port'])
        else:
            start_client(config['galc_host'], config['galc_port'])
        
        return jsonify({"message": "Configuration updated successfully"}), 200



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
