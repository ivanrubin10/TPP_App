import socket
import time
import threading
import random
import argparse
import sys
import string

def generate_sequence():
    """Generate a 3-digit sequence number"""
    return str(random.randint(100, 999))

def generate_body():
    """Generate a body in format: letter + 4 digits"""
    letter = random.choice(string.ascii_uppercase)
    digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    return f"{letter}{digits}"

def get_capot_type(key):
    """Convert key to correct capot type"""
    capot_map = {
        '1': '01',
        '2': '05',
        '3': '08'
    }
    return capot_map.get(key, random.choice(['01', '05', '08']))

def send_manual_message(conn, capot_type=None):
    """Send a single message with an optional specified capot type"""
    # Generate message components
    sequence = generate_sequence()
    body = generate_body()
    
    # Use specified capot type or random one
    if capot_type not in ['1', '2', '3']:
        capot = random.choice(['01', '05', '08'])
    else:
        capot = get_capot_type(capot_type)
    
    # Construct the full message
    message = f"{sequence}{body}{capot}"
    
    try:
        conn.sendall(message.encode())
        print(f"Sent manual PLC message: {message}")
        print(f"  - Sequence: {sequence}")
        print(f"  - Body: {body}")
        print(f"  - Capot type: {capot}")
        print("Waiting for detection result...")
        
        # Wait for response with retries
        max_retries = 20  # Try for about 20 seconds total
        for attempt in range(max_retries):
            try:
                data = conn.recv(1024)
                if not data:  # Connection closed by remote end
                    print("Connection closed by server")
                    return False
                response_byte = int.from_bytes(data, byteorder='big')
                if response_byte == 0b00000001:
                    print("Received from server: 00000001 (GOOD)")
                    break
                elif response_byte == 0b00000010:
                    print("Received from server: 00000010 (NOGOOD)")
                    break
                else:
                    print(f"Received unknown response: {bin(response_byte)}")
                    break
            except socket.timeout:
                if attempt < max_retries - 1:
                    print(f"Waiting for response... ({attempt + 1}/{max_retries})")
                    time.sleep(1)
                else:
                    print("No response received after 20 seconds")
        return True
    except (ConnectionResetError, BrokenPipeError) as e:
        print(f"Connection lost: {e}")
        return False
    except Exception as e:
        print(f"Error sending manual message: {e}")
        return False

def send_periodic_messages(conn, interval=30):
    # Function to send periodic messages to the client
    last_message = None
    
    while True:
        try:
            # Check if connection is still alive with a small message
            try:
                conn.sendall(b'\x00')  # Send null byte to test connection
            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost to server")
                return
            
            # Generate message components
            sequence = generate_sequence()
            body = generate_body()
            capot = random.choice(['01', '05', '08'])
            
            # Construct the full message
            message = f"{sequence}{body}{capot}"
            
            # Ensure we don't repeat the last message
            while message == last_message:
                sequence = generate_sequence()
                body = generate_body()
                capot = random.choice(['01', '05', '08'])
                message = f"{sequence}{body}{capot}"
            last_message = message
            
            conn.sendall(message.encode())
            print(f"Sent PLC message: {message}")
            print(f"  - Sequence: {sequence}")
            print(f"  - Body: {body}")
            print(f"  - Capot type: {capot}")
            print("Waiting for detection result...")
            
            # Wait for response with retries
            max_retries = 20  # Try for about 20 seconds total
            for attempt in range(max_retries):
                try:
                    data = conn.recv(1024)
                    if not data:  # Connection closed by remote end
                        print("Connection closed by server")
                        return
                    response_byte = int.from_bytes(data, byteorder='big')
                    if response_byte == 0b00000001:
                        print("Received from server: 00000001 (GOOD)")
                        break
                    elif response_byte == 0b00000010:
                        print("Received from server: 00000010 (NOGOOD)")
                        break
                    else:
                        print(f"Received unknown response: {bin(response_byte)}")
                        break
                except socket.timeout:
                    if attempt < max_retries - 1:
                        print(f"Waiting for response... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                    else:
                        print("No response received after 20 seconds")
            
            print(f"Next message in {interval} seconds")
            time.sleep(interval)
            
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Connection lost: {e}")
            return
        except Exception as e:
            print(f"Error sending message: {e}")
            return

def run_button_simulator(conn):
    """Simulate button presses to send car messages"""
    print("\n=== BUTTON SIMULATOR MODE ===")
    print("Press keys to simulate button presses:")
    print("1 - Send Capo Tipo 01")
    print("2 - Send Capo Tipo 05")
    print("3 - Send Capo Tipo 08")
    print("q - Quit")
    print("==============================\n")
    
    last_message = None
    detection_in_progress = False
    
    def wait_for_response():
        """Wait for response from server with timeout"""
        max_retries = 20  # Try for about 20 seconds total
        for attempt in range(max_retries):
            try:
                response = conn.recv(1024)
                if not response:  # Connection closed by remote end
                    print("\nConnection closed by server")
                    return False
                response_byte = int.from_bytes(response, byteorder='big')
                if response_byte == 0b00000001:
                    print("\nReceived from server: 00000001 (GOOD)")
                    return True
                elif response_byte == 0b00000010:
                    print("\nReceived from server: 00000010 (NOGOOD)")
                    return True
                else:
                    print(f"\nReceived unknown response: {bin(response_byte)}")
                    return True
            except socket.timeout:
                if attempt < max_retries - 1:
                    print(f"Waiting for response... ({attempt + 1}/{max_retries})", end='\r')
                    time.sleep(1)
                else:
                    print("\nNo response received after 20 seconds")
                    return False
        return False
    
    while True:
        try:
            if detection_in_progress:
                print("\nDetection in progress... Please wait.", end='\r')
                time.sleep(0.5)
                continue
                
            print("\nReady for next car. Press a button key (1/2/3/q): ", end='', flush=True)
            
            # Check if there's any pending response before accepting new input
            try:
                conn.settimeout(0.1)  # Quick check for pending data
                pending = conn.recv(1024)
                if pending:
                    print("\nReceived unexpected response, clearing buffer...")
                    continue
            except socket.timeout:
                # No pending data, proceed normally
                conn.settimeout(2.0)  # Reset timeout to normal
            except Exception:
                # Ignore other errors and proceed
                pass
            
            # Wait for user input
            key = input()
            
            if key.lower() == 'q':
                print("\nExiting button simulator...")
                break
                
            # Map key to capot type
            if key in ['1', '2', '3']:
                detection_in_progress = True
                print("\nStarting detection process...")
                
                # Generate message components
                sequence = generate_sequence()
                body = generate_body()
                capot = get_capot_type(key)
                
                # Construct the full message
                message = f"{sequence}{body}{capot}"
                
                # Ensure we don't repeat the last message
                while message == last_message:
                    sequence = generate_sequence()
                    body = generate_body()
                    capot = get_capot_type(key)
                    message = f"{sequence}{body}{capot}"
                last_message = message
                
                try:
                    # Send the message
                    conn.sendall(message.encode())
                    print(f"Message sent successfully:")
                    print(f"  - Sequence: {sequence}")
                    print(f"  - Body: {body}")
                    print(f"  - Capot type: {capot}")
                    print("\nWaiting for detection result...")
                    
                    # Wait for response
                    if wait_for_response():
                        print("\nDetection completed successfully")
                    else:
                        print("\nDetection process failed or timed out")
                    
                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"\nConnection lost while sending/receiving: {e}")
                    return
                finally:
                    detection_in_progress = False
                    print("\nSystem ready for next detection")
                    time.sleep(1)  # Brief pause to show the ready message
            else:
                print("\nInvalid key. Use 1, 2, 3, or q.")
                
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"\nConnection lost: {e}")
            break
        except Exception as e:
            print(f"\nError in button simulator: {str(e)}")
            break
    
    # Close the connection when done
    try:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
        print("Connection closed")
    except:
        pass

def handle_client(conn, addr, interval, manual_mode):
    """Handle a client connection."""
    print(f"Connected by {addr}")
    try:
        if manual_mode:
            while True:
                print("\nPress Enter to send a message, or type a capot type (1, 2, 3) and press Enter:")
                user_input = input()
                
                if user_input.lower() == 'exit':
                    break
                
                # Send message based on user input
                if not send_manual_message(conn, capot_type=user_input if user_input in ['1', '2', '3'] else None):
                    break  # Break if connection is lost
        else:
            # In automatic mode, send periodic messages
            send_periodic_messages(conn, interval)
    except ConnectionResetError:
        print("Connection reset by server")
    except Exception as e:
        print(f"Error in client handler: {e}")
    finally:
        print("Closing connection")
        try:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
        except:
            pass

def start_fake_server(host='127.0.0.1', port=12345, interval=5, mode='auto'):
    """Start a fake PLC server that sends messages."""
    print(f"Starting fake PLC server on {host}:{port}")
    server_socket = None
    
    if mode == 'auto':
        print(f"Automatic mode: Messages will be sent every {interval} seconds")
    elif mode == 'manual':
        print("Manual mode: You will need to trigger messages manually")
    elif mode == 'button':
        print("Button simulator mode: Press keys to simulate button presses")
    
    try:
        # Create a socket object
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow reuse of the address/port
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the IP and port
        server_socket.bind((host, port))
        
        # Start listening for incoming connections
        server_socket.listen(1)
        print(f"Fake PLC server listening on {host}:{port}")

        while True:
            try:
                # Wait for a connection
                conn, addr = server_socket.accept()
                conn.settimeout(2.0)  # Set timeout for receiving responses to 2 seconds
                print(f"Connected by {addr}")
                
                if mode == 'button':
                    # Run button simulator directly
                    run_button_simulator(conn)
                else:
                    # Handle client in a separate thread for auto/manual modes
                    client_thread = threading.Thread(
                        target=handle_client, 
                        args=(conn, addr, interval, mode == 'manual'),
                        daemon=True
                    )
                    client_thread.start()
                    
                    # Wait for thread to finish in manual mode
                    if mode == 'manual':
                        client_thread.join()

            except KeyboardInterrupt:
                print("\nServer shutdown requested")
                break
            except Exception as e:
                print(f"Connection error: {e}")
                print("Waiting for new connection...")
                time.sleep(2)
                
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        if server_socket:
            try:
                server_socket.close()
                print("Server socket closed")
            except:
                pass

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fake PLC Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=12345, help='Port to bind to')
    parser.add_argument('--interval', type=int, default=5, help='Interval between messages in seconds')
    parser.add_argument('--mode', choices=['auto', 'manual', 'button'], default='auto',
                        help='Operation mode: auto (periodic messages), manual (type to send), or button (simulate buttons)')
    
    args = parser.parse_args()
    
    # Start the server with the specified mode
    start_fake_server(args.host, args.port, args.interval, args.mode)
