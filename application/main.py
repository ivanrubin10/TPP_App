import time
from flask import Flask, jsonify, request, send_from_directory
import socket
import threading
from flask_socketio import SocketIO, emit
from camera import capture_image
from flask_cors import CORS
from tflite_detector import tflite_detect_image, load_tflite_model
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from dataclasses import dataclass
from ics_integration import ICSIntegration
import os
from detect_gray import detect_gray_percentage


app = Flask(__name__, static_folder='../application-ui', static_url_path='/')
CORS(app)  # Allow specific frontend

socketio = SocketIO(app, cors_allowed_origins="*")  # Allow SocketIO connections from the frontend

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///car_logs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'

db = SQLAlchemy(app)
ma = Marshmallow(app)
ics = ICSIntegration()  # Initialize ICS integration

# Cache for TFLite model and labels
model_cache = {
    'interpreter': None,
    'labels': None,
    'last_loaded': 0
}

# Function to get or load the model and labels
def get_model_and_labels():
    global model_cache
    
    # If model is not loaded or it's been more than 1 hour since last load
    current_time = time.time()
    if model_cache['interpreter'] is None or current_time - model_cache['last_loaded'] > 3600:
        print("Loading model and labels into cache...")
        try:
            # Try with application path first, fallback to current directory
            model_path = './application/detect.tflite'
            label_path = './application/labelmap.txt'
            
            if not os.path.exists(model_path):
                model_path = './detect.tflite'
                
            if not os.path.exists(label_path):
                label_path = './labelmap.txt'
            
            # Load labels
            with open(label_path, 'r') as f:
                labels = [line.strip() for line in f.readlines()]
            
            # Load model
            interpreter = load_tflite_model(model_path)
            
            # Update cache
            model_cache['interpreter'] = interpreter
            model_cache['labels'] = labels
            model_cache['last_loaded'] = current_time
            
            print(f"Model and labels loaded successfully. Found {len(labels)} labels.")
            return interpreter, labels
        except Exception as e:
            print(f"Error loading model/labels: {str(e)}")
            raise
    else:
        return model_cache['interpreter'], model_cache['labels']

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

# Define QueuedCar model for GALC cars waiting to be processed
class QueuedCar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    expected_part = db.Column(db.String(200), nullable=False)
    is_processed = db.Column(db.Boolean, default=False)

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

class QueuedCarSchema(SQLAlchemySchema):
    class Meta:
        model = QueuedCar
        load_instance = True

    id = auto_field()
    car_id = auto_field()
    date = auto_field()
    expected_part = auto_field()
    is_processed = auto_field()

car_log_schema = CarLogSchema()
car_logs_schema = CarLogSchema(many=True)
queued_car_schema = QueuedCarSchema()
queued_cars_schema = QueuedCarSchema(many=True)

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

# Initialize capturing flag
capturing = False

# Added GALC response handling and connection logic
def handle_galc_response(conn):
    global message_processing, is_connected, galc_connection
    message_processing = False
    
    # Set socket timeout for initial connection
    conn.settimeout(5.0)
    
    while True:
        try:
            socketio.emit('connection_status', {'status': True if is_connected else False})
            socketio.emit('connection_type', {'type': config['connection_type']})

            # Receive the 45-byte GALC message
            try:
                data = conn.recv(45)
                if not data:
                    print("Connection closed by GALC server")
                    break
                if len(data) != 45:
                    print(f"Warning: Unexpected GALC message length: {len(data)}. Expected 45 bytes.")
                    continue

                print(f"Received GALC message: Receiver: {data[0:6].decode()}, "
                      f"Sender: {data[6:12].decode()}, Serial: {data[12:16].decode()}, "
                      f"Trigger: {data[44]:02d}")

                # Extract and handle the last two bytes
                last_two_bytes = data[43:45]
                trigger_value = int.from_bytes(last_two_bytes, "big")  # Convert to integer
                trigger_str = f"{trigger_value:02d}"  # Ensure it is a 2-digit string

                # Only process non-empty messages (car data)
                if trigger_str in ["01", "05", "08"]:
                    # Get expected part based on trigger value
                    expected_part = {
                        "01": "Capo tipo 1",
                        "05": "Capo tipo 2",
                        "08": "Capo tipo 3"
                    }.get(trigger_str)

                    if expected_part:
                        # Generate a unique car ID
                        car_id = f"CAR_{int(time.time())}_{trigger_str}"
                        current_date = time.strftime("%d-%m-%Y %H:%M:%S")

                        # Create a new queued car entry
                        new_queued_car = QueuedCar(
                            car_id=car_id,
                            date=current_date,
                            expected_part=expected_part,
                            is_processed=False
                        )
                        
                        # Use application context for database operations
                        with app.app_context():
                            try:
                                db.session.add(new_queued_car)
                                db.session.commit()
                                # Create a dictionary representation for the socket emission
                                car_data = {
                                    'car_id': new_queued_car.car_id,
                                    'date': new_queued_car.date,
                                    'expected_part': new_queued_car.expected_part,
                                    'is_processed': new_queued_car.is_processed
                                }
                                # Notify frontend about new queued car
                                socketio.emit('new_queued_car', car_data)
                            except Exception as e:
                                print(f"Error adding queued car to database: {e}")
                                db.session.rollback()

                # Send a 26-byte response
                response = bytearray(26)
                response[:6] = data[6:12]  # Sender to receiver
                response[6:12] = data[0:6]  # Receiver to sender
                response[12:16] = data[12:16]  # Serial number
                response[25] = 0  # Always send keep-alive flag since we're just queueing
                
                try:
                    conn.sendall(response)
                    print(f"Sent GALC response: Receiver: {response[0:6].decode()}, "
                          f"Sender: {response[6:12].decode()}, Serial: {response[12:16].decode()}, "
                          f"Status: {response[25]}")
                except socket.error as e:
                    print(f"Error sending response to GALC: {e}")
                    break

            except socket.timeout:
                print("No data received from GALC within timeout")
                continue
            except ConnectionResetError:
                print("Connection reset by GALC server")
                break

        except Exception as e:
            print(f"Error handling GALC message: {e}")
            break
    
    try:
        conn.close()
    except:
        pass
    is_connected = False  # Update connection status
    galc_connection = None  # Reset GALC connection
    print("GALC connection handler terminated")

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
    global plc_connection, is_connected
    
    # Set a timeout to prevent blocking indefinitely
    conn.settimeout(1.0)
    
    while True:
        try:
            socketio.emit('connection_status', {'status': True if is_connected else False})
            socketio.emit('connection_type', {'type': config['connection_type']})
            
            try:
                # Receive data from the PLC
                data = conn.recv(1024)
                if not data:
                    print("No data received from PLC, closing connection.")
                    break

                # Decode the message
                message = data.decode(errors='replace')
                print(f"Received PLC data: {message}")
                
                # Parse the message format: SequenceBodyCapot (e.g., 123A123408)
                if len(message) >= 10:  # Ensure message is at least 10 characters
                    try:
                        # Extract parts of the message
                        sequence = message[:3]  # First 3 characters (e.g., 123)
                        body = message[3:8]     # Next 5 characters (e.g., A1234)
                        capot_type = message[8:10]  # Last 2 characters (e.g., 08)
                        
                        print(f"Parsed PLC message:")
                        print(f"  - Sequence: {sequence}")
                        print(f"  - Body: {body}")
                        print(f"  - Capot: {capot_type}")
                        
                        # Map capot type to expected part
                        expected_part = {
                            "01": "Capo tipo 1",
                            "05": "Capo tipo 2",
                            "08": "Capo tipo 3"
                        }.get(capot_type)
                        
                        if expected_part:
                            # Generate a unique car ID
                            car_id = f"PLC_{int(time.time())}_{capot_type}"
                            current_date = time.strftime("%d-%m-%Y %H:%M:%S")
                            
                            # Emit the message to the frontend
                            socketio.emit('plc_message', {'message': capot_type})
                            
                            # Create a new log entry directly (no queuing for PLC)
                            new_log = CarLog(
                                car_id=car_id,
                                date=current_date,
                                expected_part=expected_part,
                                actual_part="",  # Will be filled after detection
                                original_image_path="",  # Will be filled after detection
                                result_image_path="",  # Will be filled after detection
                                outcome=""  # Will be filled after detection
                            )
                            
                            # Use application context for database operations
                            with app.app_context():
                                try:
                                    db.session.add(new_log)
                                    db.session.commit()
                                    print(f"Added new PLC log entry with ID: {new_log.id}")
                                    
                                    # Create a dictionary for frontend notification
                                    log_dict = {
                                        'id': car_id,
                                        'expectedPart': expected_part,
                                        'actualPart': "",
                                        'outcome': "",
                                        'image': "",
                                        'resultImage': "",
                                        'date': current_date,
                                        'isQueued': False
                                    }
                                    
                                    # Notify frontend about new car
                                    socketio.emit('new_car', log_dict)
                                except Exception as e:
                                    print(f"Error adding PLC log to database: {e}")
                                    db.session.rollback()
                        else:
                            print(f"Unknown capot type: {capot_type}")
                    except Exception as e:
                        print(f"Error parsing PLC message: {e}")
                else:
                    print(f"Invalid PLC message format: {message}")
                
                # Send a response back to the PLC (can be customized based on processing result)
                response = b"OK"
                conn.sendall(response)
                print(f"Sent PLC response: {response.decode()}")
            except socket.timeout:
                # This is normal, just continue the loop
                continue
            except ConnectionResetError:
                print("Connection reset by PLC")
                break
            except Exception as e:
                print(f"Error handling PLC message: {e}")
                # Don't break the loop for other exceptions, just continue
                continue
                
        except Exception as e:
            print(f"Outer error in PLC handler: {e}")
            break
            
    print("PLC connection handler terminated")
    conn.close()
    plc_connection = None  # Reset PLC connection
    is_connected = False  # Update connection status

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
    
    # Validate input parameters if they exist
    car_id = request.args.get('car_id')
    expected_part = request.args.get('expected_part')
    actual_part = request.args.get('actual_part')
    
    print(f"Capture request received with params: car_id={car_id}, expected_part={expected_part}, actual_part={actual_part}")
    
    # Check if we have partial parameters
    if any([car_id, expected_part, actual_part]) and not all([car_id, expected_part]):
        print("Incomplete car parameters provided")
        return jsonify({'error': 'If providing car parameters, both car_id and expected_part must be provided'}), 400
    
    if capturing:
        print("Another capture is in progress, returning 429")
        return jsonify({'error': 'Another capture is in progress'}), 429  # Too Many Requests
        
    capturing = True
    start_time = time.time()
    try:
        print("Starting capture process...")
        try:
            print("Calling capture_image()...")
            image = capture_image()
            if not image:
                raise ValueError("No image data received from capture")
            print("Image captured successfully!")
        except Exception as e:
            print(f"Error during image capture: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Capture error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Image capture failed: {str(e)}'}), 500

        # Check gray percentage before proceeding
        try:
            gray_percentage = detect_gray_percentage(image)
            print(f"Gray percentage in image: {gray_percentage}%")
            
            if gray_percentage < 60:
                print("Not enough gray area detected in image")
                # Still send the captured image to the frontend
                return jsonify({
                    'image': image,  # Original image
                    'objects': [],
                    'result_image': image,  # Use original image as result image
                    'error': 'No hay capo',
                    'gray_percentage': float(gray_percentage),
                    'skip_database_update': True  # Flag to indicate frontend should not update database
                })
        except Exception as e:
            print(f"Error during gray detection: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Gray detection error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Gray detection failed: {str(e)}'}), 500
        
        # Get cached model and labels
        try:
            interpreter, labels = get_model_and_labels()
        except Exception as e:
            print(f"Error getting model/labels: {str(e)}")
            return jsonify({'error': f'Failed to load model or labels: {str(e)}'}), 500

        print(f"Using confidence threshold: {config.get('min_conf_threshold', 0.5)}")
        try:
            # Time the object detection process
            detection_start = time.time()
            result_image, detected_objects = tflite_detect_image(
                interpreter,  # Use the cached interpreter
                image, 
                labels, 
                config.get('min_conf_threshold', 0.5)
            )
            detection_time = time.time() - detection_start
            print(f"Object detection completed in {detection_time:.2f} seconds. Found {len(detected_objects)} objects")
        except Exception as e:
            print(f"Error during object detection: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Detection error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Object detection failed: {str(e)}'}), 500
        
        # Return detection results
        response_data = {
            'image': image, 
            'objects': detected_objects, 
            'result_image': result_image,
            'gray_percentage': float(gray_percentage),  # Ensure it's a float
            'processing_time': time.time() - start_time  # Add processing time for debugging
        }
        
        # Log response data without the images
        log_response = {
            'objects': detected_objects,
            'gray_percentage': float(gray_percentage),
            'processing_time': time.time() - start_time
        }
        print(f"Detection results: {log_response}")
        
        # If this is a queued car and the result will be NG, send to ICS
        if car_id and expected_part and actual_part:
            # Only send to ICS if result is NG
            if expected_part != actual_part:
                try:
                    print(f"Sending data to ICS for car_id: {car_id}")
                    vin = ics.request_vin(car_id)
                    if vin:
                        ics.send_defect_data(
                            vin=vin,
                            image_base64=result_image,
                            expected_part=expected_part,
                            actual_part=actual_part
                        )
                        print("Data sent to ICS successfully")
                except Exception as e:
                    print(f"Error sending to ICS: {str(e)}")
                    # Don't fail the whole request if ICS communication fails
        
        print(f"Capture and detect process completed in {time.time() - start_time:.2f} seconds")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in capture and detect: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
    finally:
        capturing = False  # Always reset the capturing flag
        print(f"Capture flag reset after {time.time() - start_time:.2f} seconds")

@app.route('/check-car/<car_id>', methods=['GET'])
def check_car(car_id):
    try:
        print(f"Checking if car exists with ID: {car_id}")
        car_log = CarLog.query.filter_by(car_id=car_id).first()
        if car_log:
            print(f"Found car with ID: {car_log.id}")
            return jsonify({'exists': True, 'car_log': car_log_schema.dump(car_log)})
        else:
            print(f"No car found with ID: {car_id}")
            return jsonify({'exists': False})
    except Exception as e:
        error_msg = f"Error checking car: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/update-item', methods=['PUT'])
def update_item():
    try:
        print("Received request to update item")
        data = request.get_json()
        # Create a copy of data without the image paths for logging
        log_data = {k: v for k, v in data.items() if k not in ['original_image_path', 'result_image_path']}
        print(f"Request data (excluding images): {log_data}")
        
        # Validate required fields
        required_fields = ['car_id', 'expected_part', 'actual_part', 'original_image_path', 'result_image_path', 'outcome']
        for field in required_fields:
            if field not in data or data[field] is None:
                error_msg = f"Missing required field: {field}"
                print(error_msg)
                return jsonify({'error': error_msg}), 400
        
        print(f"Looking for car with ID: {data['car_id']}")
        car_log = CarLog.query.filter_by(car_id=data['car_id']).first()
        if car_log:
            print(f"Found car with ID: {car_log.id}, updating fields")
            car_log.expected_part = data['expected_part']
            car_log.actual_part = data['actual_part']
            car_log.original_image_path = data['original_image_path']
            car_log.result_image_path = data['result_image_path']
            car_log.outcome = data['outcome']
            
            try:
                db.session.commit()
                print(f"Successfully updated car with ID: {car_log.id}")
            except Exception as e:
                db.session.rollback()
                error_msg = f"Database error during commit: {str(e)}"
                print(error_msg)
                return jsonify({'error': error_msg}), 500
            
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
            error_msg = f"Car log not found for car_id: {data['car_id']}"
            print(error_msg)
            return jsonify({'error': error_msg}), 404
    except Exception as e:
        error_msg = f"Error updating item: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/log', methods=['POST'])
def add_log():
    try:
        print("Received request to add log")
        data = request.get_json()
        # Create a copy of data without the image paths for logging
        log_data = {k: v for k, v in data.items() if k not in ['original_image_path', 'result_image_path']}
        print(f"Request data (excluding images): {log_data}")
        
        # Validate required fields
        required_fields = ['car_id', 'date', 'expected_part', 'actual_part', 'original_image_path', 'result_image_path', 'outcome']
        for field in required_fields:
            if field not in data or not data[field]:
                error_msg = f"Missing required field: {field}"
                print(error_msg)
                return jsonify({'error': error_msg}), 400
        
        # Check if car_id already exists
        existing_log = CarLog.query.filter_by(car_id=data['car_id']).first()
        if existing_log:
            error_msg = f"Car with ID {data['car_id']} already exists. Use update-item endpoint instead."
            print(error_msg)
            return jsonify({'error': error_msg}), 409  # Conflict
        
        # Create new log
        new_log = CarLog(
            car_id=data['car_id'],
            date=data['date'],
            expected_part=data['expected_part'],
            actual_part=data['actual_part'],
            original_image_path=data['original_image_path'],
            result_image_path=data['result_image_path'],
            outcome=data['outcome']
        )
        
        print(f"Adding new log for car_id: {data['car_id']}")
        db.session.add(new_log)
        db.session.commit()
        print(f"Successfully added log with ID: {new_log.id}")
        
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
        error_msg = f"Error adding log: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500


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

# Add new endpoint to get queued cars
@app.route('/queued-cars', methods=['GET'])
def get_queued_cars():
    queued_cars = QueuedCar.query.filter_by(is_processed=False).all()
    return jsonify(queued_cars_schema.dump(queued_cars))

# Add endpoint to mark a queued car as processed
@app.route('/process-queued-car/<car_id>', methods=['POST'])
def process_queued_car(car_id):
    try:
        print(f"Processing queued car with ID: {car_id}")
        queued_car = QueuedCar.query.filter_by(car_id=car_id).first()
        
        if not queued_car:
            print(f"No queued car found with ID: {car_id}")
            return jsonify({"error": "Car not found"}), 404
            
        # Mark the car as processed
        queued_car.is_processed = True
        db.session.commit()
        
        print(f"Car {car_id} marked as processed successfully")
        
        # Return the car details
        return jsonify({
            "message": "Car marked as processed",
            "car_id": queued_car.car_id,
            "expected_part": queued_car.expected_part,
            "date": queued_car.date,
            "is_processed": queued_car.is_processed
        }), 200
    except Exception as e:
        print(f"Error processing queued car: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to process car: {str(e)}"}), 500

@app.route('/send-to-ics', methods=['POST'])
def send_to_ics():
    try:
        data = request.get_json()
        car_id = data['car_id']
        expected_part = data['expected_part']
        actual_part = data['actual_part']
        # Don't log the image_base64 content
        print(f"Sending to ICS - car_id: {car_id}, expected_part: {expected_part}, actual_part: {actual_part}")
        image_base64 = data['image']

        # Get VIN and send to ICS
        vin = ics.request_vin(car_id)
        if vin:
            print(f"Retrieved VIN for car_id {car_id}: {vin}")
            result = ics.send_defect_data(
                vin=vin,
                image_base64=image_base64,
                expected_part=expected_part,
                actual_part=actual_part
            )
            if result:
                print(f"Successfully sent defect data to ICS for car_id: {car_id}")
            else:
                print(f"Failed to send defect data to ICS for car_id: {car_id}")
            return jsonify({'message': 'Sent to ICS successfully'}), 200
        print(f"Could not get VIN for car_id: {car_id}")
        return jsonify({'error': 'Could not get VIN'}), 400
    except Exception as e:
        print(f"Error in send_to_ics: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
