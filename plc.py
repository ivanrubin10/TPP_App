import socket
import time
import threading
import random
import argparse
import sys

def generate_unique_sequence():
    """Generate a unique sequence number using timestamp and random number"""
    timestamp = int(time.time() * 1000) % 10000  # Get last 4 digits of current timestamp in milliseconds
    random_num = random.randint(0, 999)  # 3-digit random number
    return f"{timestamp:04d}{random_num:03d}"[-4:]  # Take last 4 digits to maintain format

def send_manual_message(conn, capot_type=None):
    """Send a single message with an optional specified capot type"""
    # Generate a unique sequence number
    sequence = generate_unique_sequence()
    
    # Use specified capot type or random one
    if capot_type not in ['1', '2', '3']:
        capot = random.choice(['1', '2', '3'])
    else:
        capot = capot_type
    
    # Construct the full message in expected format: SEQxxxxPNyWTzz
    message = f"SEQ{sequence}PN{capot}WT01"
    
    try:
        conn.sendall(message.encode())
        print(f"Sent manual PLC message: {message}")
        print(f"  - Sequence: {sequence}")
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
    last_sequence = None
    
    while True:
        try:
            # Check if connection is still alive with a small message
            try:
                conn.sendall(b'\x00')  # Send null byte to test connection
            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost to server")
                return
            
            # Generate unique sequence
            sequence = generate_unique_sequence()
            while sequence == last_sequence:  # Ensure we don't repeat the last sequence
                sequence = generate_unique_sequence()
            last_sequence = sequence
            
            # Generate a random capot type (1, 2, or 3)
            capot = random.choice(['1', '2', '3'])
            
            # Construct the full message in expected format: SEQxxxxPNyWTzz
            message = f"SEQ{sequence}PN{capot}WT01"
            
            conn.sendall(message.encode())
            print(f"Sent PLC message: {message}")
            print(f"  - Sequence: {sequence}")
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
    print("1 - Send Capo Tipo 1")
    print("2 - Send Capo Tipo 2")
    print("3 - Send Capo Tipo 3")
    print("q - Quit")
    print("==============================\n")
    
    last_sequence = None
    
    while True:
        try:
            # Wait for a key press
            key = input("Press a button key (1/2/3/q): ")
            
            if key.lower() == 'q':
                print("Exiting button simulator...")
                break
                
            # Map key to capot type
            if key in ['1', '2', '3']:
                # Generate unique sequence
                sequence = generate_unique_sequence()
                while sequence == last_sequence:  # Ensure we don't repeat the last sequence
                    sequence = generate_unique_sequence()
                last_sequence = sequence
                
                # Construct message in the format expected by the application: SEQxxxxPNyWTzz
                message = f"SEQ{sequence}PN{key}WT01"
                
                try:
                    # Send the message
                    conn.sendall(message.encode())
                    print(f"Button press sent: {message}")
                    print(f"  - Sequence: {sequence}")
                    print(f"  - Capot type: {key}")
                    print("Waiting for detection result...")
                    
                    # Wait for response with retries
                    max_retries = 20  # Try for about 20 seconds total
                    for attempt in range(max_retries):
                        try:
                            response = conn.recv(1024)
                            if not response:  # Connection closed by remote end
                                print("Connection closed by server")
                                return
                            response_byte = int.from_bytes(response, byteorder='big')
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
                except (ConnectionResetError, BrokenPipeError) as e:
                    print(f"Connection lost while sending/receiving: {e}")
                    return
            else:
                print("Invalid key. Use 1, 2, 3, or q.")
                
        except (ConnectionResetError, BrokenPipeError) as e:
            print(f"Connection lost: {e}")
            break
        except Exception as e:
            print(f"Error in button simulator: {str(e)}")
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
