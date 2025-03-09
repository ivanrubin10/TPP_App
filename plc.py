import socket
import time
import threading
import random
import argparse
import sys

def send_manual_message(conn, capot_type=None):
    """Send a single message with an optional specified capot type"""
    sequence = random.randint(100, 999)
    body = f"A{random.randint(1000, 9999)}"
    
    # Use specified capot type or random one
    if capot_type not in ['01', '05', '08']:
        capot = random.choice(['01', '05', '08'])
    else:
        capot = capot_type
    
    # Construct the full message
    message = f"{sequence}{body}{capot}"
    
    try:
        conn.sendall(message.encode())
        print(f"Sent manual PLC message: {message}")
        print(f"  - Sequence: {sequence}")
        print(f"  - Body: {body}")
        print(f"  - Capot: {capot}")
        
        # Wait for response
        try:
            data = conn.recv(1024)
            print(f"Response from server: {data.decode()}")
        except:
            print("No response received")
    except Exception as e:
        print(f"Error sending manual message: {e}")

def send_periodic_messages(conn, interval=5):
    # Function to send periodic messages to the client
    sequence = 100  # Starting sequence number
    
    while True:
        try:
            time.sleep(interval)  # Send a message every x seconds
            
            # Increment sequence number
            sequence += 1
            
            # Generate a random body (A1234 in the example)
            body = f"A{random.randint(1000, 9999)}"
            
            # Generate a random capot type (01, 05, or 08)
            capot = random.choice(['01', '05', '08'])
            
            # Construct the full message: Sequence + Body + Capot
            message = f"{sequence}{body}{capot}"
            
            conn.sendall(message.encode())
            print(f"Sent PLC message: {message}")
            print(f"  - Sequence: {sequence}")
            print(f"  - Body: {body}")
            print(f"  - Capot: {capot}")
            print(f"  - Next message in {interval} seconds")
            
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def handle_client(conn, addr, interval, manual_mode):
    print(f"Connected by {addr}")
    
    # Start a separate thread to send periodic messages if not in manual mode
    if not manual_mode:
        message_thread = threading.Thread(target=send_periodic_messages, args=(conn, interval), daemon=True)
        message_thread.start()
        print(f"Automatic message sending started with interval of {interval} seconds")
    else:
        print("Manual mode active. Press Enter to send a message, or type 'exit' to quit.")
        print("You can also type '01', '05', or '08' to send a specific capot type.")
        
        # Start a thread to handle manual input
        def manual_input_handler():
            while True:
                try:
                    user_input = input().strip()
                    if user_input.lower() == 'exit':
                        print("Exiting...")
                        sys.exit(0)
                    elif user_input in ['01', '05', '08']:
                        send_manual_message(conn, user_input)
                    else:
                        send_manual_message(conn)
                except Exception as e:
                    print(f"Error in manual input: {e}")
                    break
        
        input_thread = threading.Thread(target=manual_input_handler, daemon=True)
        input_thread.start()
    
    # Receive and handle messages from the client
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received from client: {data.decode()}")

            # No need to send a response here as we're already responding in the message sending functions
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()

def start_fake_server(host='127.0.0.1', port=12345, interval=5, manual_mode=False):
    print(f"Starting fake PLC server on {host}:{port}")
    if manual_mode:
        print("Manual mode: You will need to trigger messages manually")
    else:
        print(f"Automatic mode: Messages will be sent every {interval} seconds")
    
    while True:
        try:
            # Create a socket object
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Bind the socket to the IP and port
            server_socket.bind((host, port))
            
            # Start listening for incoming connections
            server_socket.listen(1)
            print(f"Fake PLC server listening on {host}:{port}")

            while True:
                # Wait for a connection
                conn, addr = server_socket.accept()
                # Handle client in a separate thread
                client_thread = threading.Thread(target=handle_client, args=(conn, addr, interval, manual_mode), daemon=True)
                client_thread.start()

        except Exception as e:
            print(f"Server error: {e}")
            print("Restarting server in 5 seconds...")
            time.sleep(5)
        finally:
            server_socket.close()

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fake PLC Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=12345, help='Port to bind to')
    parser.add_argument('--interval', type=int, default=5, help='Interval between messages in seconds')
    parser.add_argument('--manual', action='store_true', help='Manual mode - send messages on demand')
    
    args = parser.parse_args()
    
    start_fake_server(args.host, args.port, args.interval, args.manual)
