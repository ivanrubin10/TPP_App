from flask import Flask, jsonify, request, send_from_directory
import socket
import threading
from flask_socketio import SocketIO, emit
from camera import capture_image, create_placeholder_image
from flask_cors import CORS
from tflite_detector import tflite_detect_image, load_tflite_model
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from dataclasses import dataclass
from ics_integration import ICSIntegration
import os
import base64
import json
import time
from detect_gray import detect_gray_percentage
import cv2
import numpy as np
import logging
import subprocess
from datetime import datetime
import uuid
import requests
import traceback  # Add traceback import

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

def get_model_and_labels():
    """
    Load the TFLite model and labels for object detection.
    
    Returns:
        tuple: (model, class_names)
    """
    print("Loading TFLite model and labels...")
    # Try with application path first, fallback to current directory
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'detect.tflite')
    label_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'labelmap.txt')
    
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}, trying current directory")
        model_path = 'detect.tflite'
        
    if not os.path.exists(label_path):
        print(f"Labels not found at {label_path}, trying current directory")
        label_path = 'labelmap.txt'
    
    # Load labels
    with open(label_path, 'r') as f:
        class_names = [line.strip() for line in f.readlines()]
        print(f"Loaded {len(class_names)} labels")
    
    # Load model using TFLite
    model = load_tflite_model(model_path)
    print("TFLite model loaded successfully")
    
    return model, class_names

# Define CarLog model
class CarLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.String(50), unique=True, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    expected_part = db.Column(db.String(200), nullable=False)
    actual_part = db.Column(db.String(200), nullable=False)
    original_image = db.Column(db.Text, nullable=False)  # Store base64 image directly
    result_image = db.Column(db.Text, nullable=False)    # Store base64 image directly
    outcome = db.Column(db.String(200), nullable=False)
    gray_percentage = db.Column(db.Float)
    
    # Add index for faster lookups
    __table_args__ = (
        db.Index('idx_car_id', 'car_id'),
    )

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
    original_image = auto_field()
    result_image = auto_field()
    outcome = auto_field()
    gray_percentage = auto_field()

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
    db.create_all()  # Create tables if they don't exist

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
    "galc_port": 54321,       # Default GALC port
    "image_source": "camera"  # Options: "camera", "no_capo", "capo_tipo_1", "capo_tipo_2", "capo_tipo_3"
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

def send_plc_response(socket, is_good):
    """
    Send response byte to PLC based on detection result.
    Args:
        socket: The PLC socket connection
        is_good (bool): True if detection result is GOOD, False if NOGOOD
    """
    try:
        # Create response byte: 00000001 for GOOD, 00000010 for NOGOOD
        response_byte = bytes([0b00000001]) if is_good else bytes([0b00000010])
        socket.sendall(response_byte)
        print(f"Sent response to PLC: {bin(response_byte[0])} ({'GOOD' if is_good else 'NOGOOD'})")
    except Exception as e:
        print(f"Error sending response to PLC: {str(e)}")

def handle_plc_response(plc_socket):
    """Handle responses from the PLC socket."""
    global is_connected, plc_connection
    print("\n=== Starting PLC response handler ===")
    print(f"Initial connection status: {is_connected}")
    
    plc_socket.settimeout(0.5)
    print("Socket timeout set to 0.5 seconds")
    
    message_count = 0
    processed_cars = set()  # Keep track of processed car IDs
    
    while True:
        try:
            if not is_connected:
                print("Connection marked as disconnected, exiting handler")
                break

            print(f"\n--- Waiting for PLC message (count: {message_count}) ---")
            socketio.emit('connection_status', {'service': 'PLC', 'status': 'Conectado'})
            socketio.emit('connection_type', {'type': 'PLC'})

            try:
                print("Attempting to receive data from PLC...")
                data = plc_socket.recv(1024)
                
                if not data:
                    print("WARNING: Received empty data from PLC")
                    socketio.emit('connection_status', {'service': 'PLC', 'status': 'Desconectado'})
                    break

                print(f"Raw data received from PLC: {data}")
                message = data.decode('UTF-8')
                print(f"Decoded PLC message: {message}")
                message_count += 1
                
                if len(message) < 10:
                    print(f"WARNING: Invalid message format (too short): {message}")
                    continue
                
                # Extract sequence and part type from message
                try:
                    print("\n=== Parsing message ===")
                    sequence = message[3:7]  # Get the sequence number after "SEQ"
                    print(f"Extracted sequence: {sequence}")
                    
                    pn_pos = message.find("PN")  # Find the position of "PN"
                    print(f"Found PN at position: {pn_pos}")
                    
                    if pn_pos == -1:
                        print("ERROR: Invalid message format: PN not found")
                        continue
                        
                    capot_type = message[pn_pos + 2]  # Get the number after "PN"
                    print(f"Extracted capot type: {capot_type}")
                    
                    expected_part = {
                        "1": "Capo tipo 1",
                        "2": "Capo tipo 2",
                        "3": "Capo tipo 3"
                    }.get(capot_type)
                    
                    if not expected_part:
                        print(f"ERROR: Unknown capot type: {capot_type}")
                        continue

                    car_id = f"{sequence}-{message[pn_pos:]}"
                    
                    # Check if we've already processed this car
                    if car_id in processed_cars:
                        print(f"WARNING: Car {car_id} has already been processed, skipping")
                        continue
                        
                    current_time = time.strftime("%d-%m-%Y %H:%M:%S")
                    print(f"\n=== Processing car ===")
                    print(f"Generated car_id: {car_id}")
                    print(f"Expected part: {expected_part}")
                    print(f"Timestamp: {current_time}")

                    with app.app_context():
                        print("\n=== Database operations ===")
                        try:
                            # Check if car already exists using a single query with FOR UPDATE
                            existing_car = db.session.query(CarLog).filter_by(car_id=car_id).with_for_update().first()
                            
                            if existing_car:
                                print(f"WARNING: Car {car_id} already exists in database, skipping")
                                processed_cars.add(car_id)  # Add to processed set
                                db.session.rollback()  # Release the lock
                                continue

                            print("Creating new car entry...")
                            # Create initial car entry
                            new_car = CarLog(
                                car_id=car_id,
                                date=current_time,
                                expected_part=expected_part,
                                actual_part="Pendiente",
                                original_image="",
                                result_image="",
                                outcome="Pendiente",
                                gray_percentage=None
                            )
                            
                            db.session.add(new_car)
                            db.session.commit()
                            processed_cars.add(car_id)  # Add to processed set
                            print(f"Successfully added car {car_id} to database")
                            
                            print("Notifying frontend about new car...")
                            socketio.emit('new_car', {
                                'car_id': car_id,
                                'date': current_time,
                                'expected_part': expected_part
                            })
                            
                            print("Waiting for camera...")
                            time.sleep(1)  # Wait for camera
                            
                            print(f"\n=== Starting detection for car {car_id} ===")
                            try:
                                # Get image based on configured source
                                print(f"Image source configured as: {config['image_source']}")
                                if config['image_source'] == 'camera':
                                    print("Capturing image from camera...")
                                    image_base64 = capture_image()
                                else:
                                    print(f"Loading sample image: {config['image_source']}")
                                    image_base64 = load_sample_image(config['image_source'])

                                if not image_base64:
                                    raise Exception("Failed to get image")

                                print("Calculating gray percentage...")
                                gray_percentage = calculate_gray_percentage(image_base64)
                                print(f"Gray percentage calculated: {gray_percentage:.2f}%")
                                
                                # Initialize variables
                                actual_part = None
                                detected_objects = []
                                result_image = image_base64  # Default to original image
                                
                                if gray_percentage >= 60:
                                    print("Gray percentage >= 60%, proceeding with detection...")
                                    # Load model and labels
                                    model, labels = get_model_and_labels()
                                    
                                    # Perform detection
                                    print("Running object detection...")
                                    result_image, detected_objects = tflite_detect_image(
                                        model, 
                                        image_base64, 
                                        labels, 
                                        min_conf=0.5,
                                        early_exit=False
                                    )
                                    
                                    print(f"Detection complete. Found {len(detected_objects)} objects")
                                    
                                    # Count specific objects
                                    has_amorfo = any(obj['class'].lower() == 'amorfo' and obj['score'] > 0.5 for obj in detected_objects)
                                    has_chico = any(obj['class'].lower() == 'chico' and obj['score'] > 0.5 for obj in detected_objects)
                                    has_mediano = any(obj['class'].lower() == 'mediano' and obj['score'] > 0.5 for obj in detected_objects)
                                    has_grande = any(obj['class'].lower() == 'grande' and obj['score'] > 0.5 for obj in detected_objects)
                                    
                                    print("\n=== Detection Results ===")
                                    print(f"Detected objects: {[obj['class'] for obj in detected_objects]}")
                                    print(f"Scores: {[obj['score'] for obj in detected_objects]}")
                                    print(f"Amorfo detected: {has_amorfo}")
                                    print(f"Chico detected: {has_chico}")
                                    print(f"Mediano detected: {has_mediano}")
                                    print(f"Grande detected: {has_grande}")
                                    
                                    # Apply detection rules
                                    if any(obj['class'].lower() == 'amorfo' for obj in detected_objects):  # Changed condition
                                        actual_part = "Capo tipo 2"
                                        print("Classified as: Capo tipo 2 (has amorfo)")
                                    elif has_chico and has_mediano and has_grande:
                                        actual_part = "Capo tipo 3"
                                        print("Classified as: Capo tipo 3 (has all three holes)")
                                    elif len(detected_objects) == 0:
                                        actual_part = "Capo tipo 1"
                                        print("Classified as: Capo tipo 1 (no holes detected)")
                                    else:
                                        actual_part = "Capo no identificado"
                                        print("Classified as: Capo no identificado (ambiguous pattern)")
                                        print("Detected objects:", [f"{obj['class']} (score: {obj['score']:.2f})" for obj in detected_objects])
                                else:
                                    print("No capo detected - gray percentage below 60%")
                                    actual_part = "No hay capo"
                                
                                # Determine outcome
                                outcome = "GOOD" if actual_part == expected_part else "NOGOOD"
                                print(f"\n=== Final Result ===")
                                print(f"Expected part: {expected_part}")
                                print(f"Actual part: {actual_part}")
                                print(f"Outcome: {outcome}")
                                
                                print("Sending response to PLC...")
                                send_plc_response(plc_socket, outcome == "GOOD")
                                
                                print("\n=== Updating database ===")
                                # Update car in database with complete results
                                car = CarLog.query.filter_by(car_id=car_id).first()
                                if car:
                                    print(f"Updating car {car_id} with detection results...")
                                    car.actual_part = actual_part
                                    car.outcome = outcome
                                    car.original_image = image_base64
                                    car.result_image = result_image
                                    car.gray_percentage = gray_percentage
                                    db.session.commit()
                                    print("Database update successful")
                                    
                                    print("Notifying frontend with complete results...")
                                    socketio.emit('detection_complete', {
                                        'car_id': car_id,
                                        'actual_part': actual_part,
                                        'outcome': outcome,
                                        'original_image': image_base64,
                                        'result_image': result_image,
                                        'gray_percentage': gray_percentage
                                    })
                                    
                                    print(f"Detection process completed for car {car_id}")
                                    
                                    if outcome == "NOGOOD" and 'capo' in actual_part.lower():
                                        print(f"Sending NOGOOD result to ICS for car {car_id}")
                                        vin = ics.request_vin(car_id)
                                        if vin:
                                            ics.send_defect_data(vin, image_base64, expected_part, actual_part)
                            
                            except Exception as e:
                                print(f"ERROR during detection process: {str(e)}")
                                car = CarLog.query.filter_by(car_id=car_id).first()
                                if car:
                                    car.actual_part = "Error en detección"
                                    car.outcome = "Error"
                                    db.session.commit()
                                    socketio.emit('detection_error', {
                                        'car_id': car_id,
                                        'error': str(e)
                                    })
                                    print("Sending NOGOOD response to PLC due to error")
                                    send_plc_response(plc_socket, False)
                        
                        except Exception as e:
                            print(f"ERROR in database operation: {str(e)}")
                            traceback.print_exc()
                            db.session.rollback()
                            continue
                            
                except Exception as e:
                    print(f"ERROR parsing message: {str(e)}")
                    traceback.print_exc()
                    continue
            
            except socket.timeout:
                continue
            except ConnectionResetError:
                print("ERROR: PLC connection reset")
                traceback.print_exc()
                socketio.emit('connection_status', {'service': 'PLC', 'status': 'Desconectado'})
                break
            except Exception as e:
                print(f"ERROR in PLC handler: {str(e)}")
                traceback.print_exc()
                try:
                    socketio.emit('connection_status', {'service': 'PLC', 'status': 'Error'})
                except:
                    pass
                break

        except Exception as e:
            print(f"ERROR in main PLC handler loop: {str(e)}")
            traceback.print_exc()
            break
    
    print("\n=== PLC handler terminating ===")
    print("Cleaning up connection...")
    is_connected = False
    plc_connection = None
    try:
        plc_socket.close()
        print("Socket closed successfully")
    except:
        print("Error closing socket")
    print("PLC handler terminated")

def connect_to_plc():
    global client_socket, is_connected, plc_connection

    if plc_connection is not None:
        print("Already connected to PLC. Ignoring new connection attempt.")
        return

    host = config["plc_host"]
    port = config["plc_port"]
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"\n=== PLC Connection Attempt {attempt + 1}/{max_retries} ===")
            print(f"Trying to connect to PLC at {host}:{port}")
            
            # Create socket with timeout
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(5)  # 5 second timeout for connection attempts
            
            # Attempt connection
            conn.connect((host, port))
            
            print("Successfully connected to PLC")
            client_socket = conn
            plc_connection = conn
            is_connected = True
            
            # Update frontend about successful connection
            socketio.emit('connection_status', {
                'service': 'PLC',
                'status': 'Conectado',
                'host': host,
                'port': port
            })
            
            # Start handler thread
            threading.Thread(target=handle_plc_response, args=(conn,), daemon=True).start()
            return True
            
        except socket.timeout:
            error_msg = f"Connection attempt {attempt + 1} timed out"
            print(error_msg)
            socketio.emit('connection_status', {
                'service': 'PLC',
                'status': 'Error',
                'error': error_msg
            })
            
        except ConnectionRefusedError:
            error_msg = f"Connection refused - Is the PLC simulator running at {host}:{port}?"
            print(error_msg)
            socketio.emit('connection_status', {
                'service': 'PLC',
                'status': 'Error',
                'error': error_msg
            })
            
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            print(error_msg)
            socketio.emit('connection_status', {
                'service': 'PLC',
                'status': 'Error',
                'error': error_msg
            })
        
        # Clean up failed connection attempt
        try:
            if 'conn' in locals():
                conn.close()
        except:
            pass
        
        if attempt < max_retries - 1:  # Don't sleep after last attempt
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("\n=== PLC Connection Failed ===")
    print(f"Could not connect to PLC at {host}:{port} after {max_retries} attempts")
    is_connected = False
    return False

def retry_connection():
    global client_socket, is_connected, plc_connection, galc_connection
    
    print("Retrying connection...")
    
    # Close existing connections
    if plc_connection:
        try:
            plc_connection.shutdown(socket.SHUT_RDWR)
            plc_connection.close()
        except:
            pass
        plc_connection = None
        
    if galc_connection:
        try:
            galc_connection.shutdown(socket.SHUT_RDWR)
            galc_connection.close()
        except:
            pass
        galc_connection = None
        
    if client_socket:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
            client_socket.close()
        except:
            pass
        client_socket = None
    
    is_connected = False
    socketio.emit('connection_status', {'status': False})
    
    # Wait a moment for connections to close
    time.sleep(1)
    
    # Attempt to reconnect
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

def process_detection(image_base64, expected_part):
    """
    Process image detection with consistent rules.
    Returns tuple of (actual_part, result_image, detected_objects, gray_percentage)
    """
    # Calculate gray percentage
    gray_percentage = calculate_gray_percentage(image_base64)
    print(f"Gray percentage: {gray_percentage:.2f}%")
    
    # Initialize variables
    actual_part = None
    detected_objects = []
    result_image = image_base64  # Default to original image
    
    if gray_percentage < 60:
        print("No capo detected - gray percentage below 60%")
        actual_part = "No hay capo"
        return actual_part, result_image, detected_objects, gray_percentage
    
    # Load model and labels
    model, labels = get_model_and_labels()
    
    # Perform detection
    result_image, detected_objects = tflite_detect_image(
        model, 
        image_base64, 
        labels, 
        min_conf=0.5,
        early_exit=False
    )
    
    # Count specific objects
    has_amorfo = any(obj['class'].lower() == 'amorfo' and obj['score'] > 0.5 for obj in detected_objects)
    has_chico = any(obj['class'].lower() == 'chico' and obj['score'] > 0.5 for obj in detected_objects)
    has_mediano = any(obj['class'].lower() == 'mediano' and obj['score'] > 0.5 for obj in detected_objects)
    has_grande = any(obj['class'].lower() == 'grande' and obj['score'] > 0.5 for obj in detected_objects)
    
    # Apply detection rules
    if has_amorfo:  # If any amorfo object is detected, it's tipo 2
        actual_part = "Capo tipo 2"
    elif has_chico and has_mediano and has_grande:
        actual_part = "Capo tipo 3"
    elif len(detected_objects) == 0:
        actual_part = "Capo tipo 1"
    else:
        actual_part = "Capo no identificado"
    
    return actual_part, result_image, detected_objects, gray_percentage

@app.route("/capture-image", methods=['GET', 'POST'])
def capture_and_detect():
    # Extract parameters from either GET or POST request
    if request.method == 'POST':
        data = request.get_json()
        car_id = data.get('car_id', '')
        expected_part = data.get('expected_part', '')
    else:
        car_id = request.args.get('car_id', '')
        expected_part = request.args.get('expected_part', '')
    
    print(f"Capture request received for car_id: {car_id}, expected_part: {expected_part}")
    
    try:
        start_time = time.time()
        
        # Get image based on configured source
        if config['image_source'] == 'camera':
            print("Using camera to capture image")
            base64_image = capture_image()
        else:
            print(f"Using sample image: {config['image_source']}")
            base64_image = load_sample_image(config['image_source'])
        
        # Calculate gray percentage
        gray_percentage = calculate_gray_percentage(base64_image)
        print(f"Gray percentage: {gray_percentage:.2f}%")
        
        # Initialize variables
        actual_part = None
        detected_objects = []
        result_image = base64_image  # Default to original image
        
        if gray_percentage >= 60:
            # Load model and labels
            model, labels = get_model_and_labels()
            
            # Perform detection
            result_image, detected_objects = tflite_detect_image(
                model, 
                base64_image, 
                labels, 
                min_conf=0.5,
                early_exit=False
            )
            
            # Count specific objects
            has_amorfo = any(obj['class'].lower() == 'amorfo' and obj['score'] > 0.5 for obj in detected_objects)
            has_chico = any(obj['class'].lower() == 'chico' and obj['score'] > 0.5 for obj in detected_objects)
            has_mediano = any(obj['class'].lower() == 'mediano' and obj['score'] > 0.5 for obj in detected_objects)
            has_grande = any(obj['class'].lower() == 'grande' and obj['score'] > 0.5 for obj in detected_objects)
            
            # Apply detection rules
            if has_amorfo:  # If any amorfo object is detected, it's tipo 2
                actual_part = "Capo tipo 2"
            elif has_chico and has_mediano and has_grande:
                actual_part = "Capo tipo 3"
            elif len(detected_objects) == 0:
                actual_part = "Capo tipo 1"
            else:
                actual_part = "Capo no identificado"
        else:
            print("No capo detected - gray percentage below 60%")
            actual_part = "No hay capo"
        
        # Determine outcome
        outcome = "GOOD" if expected_part == actual_part else "NOGOOD"
        
        # Log the detection in the database if car_id is provided
        if car_id:
            log_data = {
                'car_id': car_id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'expected_part': expected_part,
                'actual_part': actual_part,
                'original_image': base64_image,
                'result_image': result_image,
                'outcome': outcome,
                'gray_percentage': gray_percentage
            }
            
            existing_car = CarLog.query.filter_by(car_id=car_id).first()
            if existing_car:
                for key, value in log_data.items():
                    setattr(existing_car, key, value)
                db.session.commit()
                
                # Notify frontend to update with final result
                socketio.emit('detection_complete', {
                    'car_id': car_id,
                    'actual_part': actual_part,
                    'outcome': outcome,
                    'original_image': base64_image,
                    'result_image': result_image,
                    'gray_percentage': gray_percentage
                })
            else:
                new_log = CarLog(**log_data)
                db.session.add(new_log)
                db.session.commit()
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Return the final results
        return jsonify({
            'image': base64_image,
            'objects': detected_objects,
            'result_image': result_image,
            'gray_percentage': gray_percentage,
            'processing_time': processing_time,
            'actual_part': actual_part,
            'outcome': outcome,
            'skip_database_update': False
        })
    
    except Exception as e:
        print(f"Error in capture_and_detect: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/check-car/<car_id>', methods=['GET'])
def check_car(car_id):
    try:
        print(f"Checking if car exists with ID: {car_id}")
        car_log = CarLog.query.filter_by(car_id=car_id).first()
        if car_log:
            print(f"Found car with ID: {car_log.id}, actual_part: {car_log.actual_part}, outcome: {car_log.outcome}")
            result = car_log_schema.dump(car_log)
            # Ensure we're returning complete data
            result['actual_part'] = car_log.actual_part
            result['outcome'] = car_log.outcome
            result['gray_percentage'] = car_log.gray_percentage
            return jsonify({'exists': True, 'car_log': result})
        else:
            print(f"No car found with ID: {car_id}")
            return jsonify({'exists': False})
    except Exception as e:
        error_msg = f"Error checking car: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({'error': error_msg}), 500

@app.route('/update-item', methods=['PUT'])
def update_item():
    """Update an existing log entry"""
    try:
        data = request.get_json()
        print(f"Updating item with data: {data}")
        
        # Validate car_id
        if 'car_id' not in data or not data['car_id']:
            return jsonify({'error': 'Missing car_id'}), 400
        
        # Find the car log
        car_log = CarLog.query.filter_by(car_id=data['car_id']).first()
        if not car_log:
            return jsonify({'error': f"Car with ID {data['car_id']} not found"}), 404
        
        # Update fields
        for key, value in data.items():
            if hasattr(car_log, key) and key != 'id':
                setattr(car_log, key, value)
                print(f"Updated {key} to {value}")
        
        db.session.commit()
        print(f"Database updated successfully for car_id: {data['car_id']}")
        
        # Return updated car log with complete data
        result = car_log_schema.dump(car_log)
        result['actual_part'] = car_log.actual_part
        result['outcome'] = car_log.outcome
        result['gray_percentage'] = car_log.gray_percentage
        return jsonify(result)
    except Exception as e:
        print(f"Error updating item: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def add_inspection_log(expected_part, actual_part, outcome, gray_percentage=None):
    """
    Add a new car inspection log to the database.
    """
    try:
        # Create a unique car ID
        car_id = f"AUTO_{int(time.time())}"
        current_date = time.strftime("%d-%m-%Y %H:%M:%S")
        
        log = CarLog(
            car_id=car_id,
            date=current_date,
            expected_part=expected_part,
            actual_part=actual_part,
            original_image="",  # Will be updated later
            result_image="",    # Will be updated later
            outcome=outcome,
            gray_percentage=float(gray_percentage) if gray_percentage is not None else None
        )
        
        db.session.add(log)
        db.session.commit()
        return log.id
    except Exception as e:
        db.session.rollback()
        print(f"Error adding log: {str(e)}")
        raise

@app.route('/log', methods=['POST'])
def add_log():
    """Add a new log entry"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['car_id', 'date', 'expected_part', 'actual_part', 'original_image', 'result_image', 'outcome']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if car_id already exists
        existing_log = CarLog.query.filter_by(car_id=data['car_id']).first()
        if existing_log:
            # Update existing log
            for key, value in data.items():
                if hasattr(existing_log, key):
                    setattr(existing_log, key, value)
            db.session.commit()
            return jsonify({'message': 'Log updated successfully', 'id': existing_log.id})
        
        # Create new log
        new_log = CarLog(
            car_id=data['car_id'],
            date=data['date'],
            expected_part=data['expected_part'],
            actual_part=data['actual_part'],
            original_image=data['original_image'],
            result_image=data['result_image'],
            outcome=data['outcome'],
            gray_percentage=data.get('gray_percentage')
        )
        
        db.session.add(new_log)
        db.session.commit()
        
        return jsonify({'message': 'Log added successfully', 'id': new_log.id})
    except Exception as e:
        print(f"Error adding log: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """Get all logs"""
    try:
        logs = CarLog.query.all()
        car_log_schema = CarLogSchema(many=True)
        return jsonify(car_log_schema.dump(logs))
    except Exception as e:
        print(f"Error getting logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        if 'image_source' in data:
            # Validate image_source value
            valid_sources = ["camera", "no_capo", "capo_tipo_1", "capo_tipo_2", "capo_tipo_3"]
            if data['image_source'] in valid_sources:
                config['image_source'] = str(data['image_source'])
            else:
                return jsonify({"error": f"image_source must be one of: {', '.join(valid_sources)}"}), 400
        
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

def calculate_gray_percentage(base64_image):
    """
    Calculate the percentage of the image that is gray/white (for detecting presence of a capot).
    
    Args:
        base64_image (str): Base64 encoded image string
        
    Returns:
        float: Percentage of pixels that are gray/white
    """
    try:
        # Decode base64 image
        if isinstance(base64_image, str) and ',' in base64_image:
            base64_image = base64_image.split(',')[1]
        
        img_data = base64.b64decode(base64_image)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Failed to decode image in calculate_gray_percentage")
            return 0.0
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply a threshold to identify gray/white pixels
        # Threshold value is chosen to isolate the light gray capot from darker background
        threshold_value = 100  # Adjust if needed for your specific application
        _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
        
        # Calculate percentage of white pixels
        white_pixel_count = cv2.countNonZero(thresh)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        percentage = (white_pixel_count / total_pixels) * 100
        
        return percentage
    except Exception as e:
        print(f"Error calculating gray percentage: {str(e)}")
        return 0.0

def mark_low_gray_percentage_image(base64_image, gray_percentage):
    """
    Return the original image without any modifications.
    
    Args:
        base64_image (str): Base64 encoded image string
        gray_percentage (float): The calculated gray percentage (not used)
        
    Returns:
        str: Original base64 encoded image string
    """
    # Simply return the original image without any modifications
    return base64_image

@app.route('/reset-database', methods=['POST'])
def reset_database():
    """Reset and recreate database tables"""
    try:
        # Drop all tables
        db.drop_all()
        # Create all tables with new schema
        db.create_all()
        return jsonify({'message': 'Database reset successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add this function to load sample images
def load_sample_image(image_type):
    """
    Load a sample image based on the specified type.
    
    Args:
        image_type (str): Type of image to load ('no_capo', 'capo_tipo_1', 'capo_tipo_2', 'capo_tipo_3')
        
    Returns:
        str: Base64 encoded image string
    """
    # Map image types to file paths
    image_paths = {
        'no_capo': os.path.join('sample_images', 'no_capo.jpg'),
        'capo_tipo_1': os.path.join('sample_images', 'capo_tipo_1.jpg'),
        'capo_tipo_2': os.path.join('sample_images', 'capo_tipo_2.jpg'),
        'capo_tipo_3': os.path.join('sample_images', 'capo_tipo_3.jpg')
    }
    
    # Get the path for the requested image type
    if image_type not in image_paths:
        print(f"Invalid image type: {image_type}")
        # Create a blank image as fallback
        blank_img = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_img.fill(200)  # Light gray
        # Add text to indicate error
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(blank_img, f"Invalid image type: {image_type}", (50, 240), font, 1, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', blank_img)
        return base64.b64encode(buffer).decode('utf-8')
    
    image_path = image_paths[image_type]
    
    # Check if the file exists in the application directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(app_dir, image_path)
    
    if not os.path.exists(full_path):
        print(f"Sample image not found: {full_path}")
        # Create a placeholder image with text
        placeholder_img = np.zeros((480, 640, 3), dtype=np.uint8)
        placeholder_img.fill(200)  # Light gray
        
        # Add text to indicate missing file
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(placeholder_img, f"Sample image not found: {image_type}", (50, 240), font, 1, (0, 0, 255), 2)
        cv2.putText(placeholder_img, f"Create file: {full_path}", (50, 280), font, 0.7, (0, 0, 255), 2)
        
        _, buffer = cv2.imencode('.jpg', placeholder_img)
        return base64.b64encode(buffer).decode('utf-8')
    
    # Read and encode the image
    try:
        with open(full_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"Error loading sample image: {str(e)}")
        # Create an error image
        error_img = np.zeros((480, 640, 3), dtype=np.uint8)
        error_img.fill(200)  # Light gray
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(error_img, f"Error loading image: {str(e)}", (50, 240), font, 0.8, (0, 0, 255), 2)
        _, buffer = cv2.imencode('.jpg', error_img)
        return base64.b64encode(buffer).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
