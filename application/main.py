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
    
    if capturing:
        print("Another capture is in progress, returning 429")
        return jsonify({'error': 'Another capture is in progress'}), 429  # Too Many Requests
        
    capturing = True
    try:
        print("Starting capture process...")
        try:
            print("Calling capture_image()...")
            image = capture_image()
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
                return jsonify({
                    'image': image,
                    'objects': [],
                    'result_image': image,
                    'error': 'No hay capo',
                    'gray_percentage': float(gray_percentage)
                })
        except Exception as e:
            print(f"Error during gray detection: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Gray detection error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Gray detection failed: {str(e)}'}), 500
        
        print("Loading model and label files...")
        # Try with application path first, fallback to current directory
        try:
            model_path = './application/detect.tflite'
            label_path = './application/labelmap.txt'
            print(f"Attempting to load files from application directory: {model_path}, {label_path}")
            
            if not os.path.exists(model_path):
                print(f"Model file not found at {model_path}")
                model_path = './detect.tflite'
                print(f"Trying alternate path: {model_path}")
                
            if not os.path.exists(label_path):
                print(f"Label file not found at {label_path}")
                label_path = './labelmap.txt'
                print(f"Trying alternate path: {label_path}")
            
            with open(label_path, 'r') as f:
                labels = [line.strip() for line in f.readlines()]
                print(f"Loaded {len(labels)} labels: {labels}")
        except Exception as e:
            print(f"Error loading model/label files: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Model loading error traceback: {traceback.format_exc()}")
            return jsonify({'error': f'Failed to load model or labels: {str(e)}'}), 500

        print(f"Files loaded successfully. Using confidence threshold: {config.get('min_conf_threshold', 0.5)}")
        try:
            result_image, detected_objects = tflite_detect_image(
                model_path, 
                image, 
                labels, 
                config.get('min_conf_threshold', 0.5)
            )
            print(f"Objects detected successfully! Found {len(detected_objects)} objects")
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
            'gray_percentage': float(gray_percentage)  # Ensure it's a float
        }
        
        # If this is a queued car and the result will be NG, send to ICS
        if request.args.get('car_id') and request.args.get('expected_part') and request.args.get('actual_part'):
            car_id = request.args.get('car_id')
            expected_part = request.args.get('expected_part')
            actual_part = request.args.get('actual_part')
            
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
        
        print("Capture and detect process completed successfully")
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
        print("Capture flag reset")

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

# Add new endpoint to get queued cars
@app.route('/queued-cars', methods=['GET'])
def get_queued_cars():
    queued_cars = QueuedCar.query.filter_by(is_processed=False).all()
    return jsonify(queued_cars_schema.dump(queued_cars))

# Add endpoint to mark a queued car as processed
@app.route('/process-queued-car/<car_id>', methods=['POST'])
def process_queued_car(car_id):
    queued_car = QueuedCar.query.filter_by(car_id=car_id).first()
    if queued_car:
        queued_car.is_processed = True
        db.session.commit()
        return jsonify({"message": "Car marked as processed"}), 200
    return jsonify({"error": "Car not found"}), 404

@app.route('/send-to-ics', methods=['POST'])
def send_to_ics():
    try:
        data = request.get_json()
        car_id = data['car_id']
        expected_part = data['expected_part']
        actual_part = data['actual_part']
        image_base64 = data['image']

        # Get VIN and send to ICS
        vin = ics.request_vin(car_id)
        if vin:
            ics.send_defect_data(
                vin=vin,
                image_base64=image_base64,
                expected_part=expected_part,
                actual_part=actual_part
            )
            return jsonify({'message': 'Sent to ICS successfully'}), 200
        return jsonify({'error': 'Could not get VIN'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
