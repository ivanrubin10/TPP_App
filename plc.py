import socket
import time
import threading
import random
import argparse
import sys

def send_manual_message(conn, capot_type=None):
    """Send a single message with an optional specified capot type"""
    # Generate a random sequence number
    sequence = random.randint(1000, 9999)
    seq_str = f"{sequence:04d}"
    
    # Use specified capot type or random one
    if capot_type not in ['1', '2', '3']:
        capot = random.choice(['1', '2', '3'])
    else:
        capot = capot_type
    
    # Construct the full message in expected format: SEQxxxxPNyWTzz
    message = f"SEQ{seq_str}PN{capot}WT01"
    
    try:
        conn.sendall(message.encode())
        print(f"Sent manual PLC message: {message}")
        print(f"  - Sequence: {seq_str}")
        print(f"  - Capot type: {capot}")
        
        # Wait for response
        try:
            data = conn.recv(1024)
            print(f"Response from server: {data.decode()}")
        except:
            print("No response received")
    except Exception as e:
        print(f"Error sending manual message: {e}")

def send_periodic_messages(conn, interval=30):
    # Function to send periodic messages to the client
    sequence = 1000  # Starting sequence number
    
    while True:
        try:
            time.sleep(interval)  # Send a message every x seconds
            
            # Increment sequence number
            sequence += 1
            seq_str = f"{sequence:04d}"  # Format as 4 digits
            
            # Generate a random capot type (1, 2, or 3)
            capot = random.choice(['1', '2', '3'])
            
            # Construct the full message in expected format: SEQxxxxPNyWTzz
            message = f"SEQ{seq_str}PN{capot}WT01"
            
            conn.sendall(message.encode())
            print(f"Sent PLC message: {message}")
            print(f"  - Sequence: {seq_str}")
            print(f"  - Capot type: {capot}")
            print(f"  - Next message in {interval} seconds")
            
        except Exception as e:
            print(f"Error sending message: {e}")
            break

def run_button_simulator(conn):
    """Simulate button presses to send car messages"""
    print("\n=== BUTTON SIMULATOR MODE ===")
    print("Press keys to simulate button presses:")
    print("1 - Send Capo Tipo 1")
    print("2 - Send Capo Tipo 2")
    print("3 - Send Capo Tipo 3")
    print("q - Quit")
    print("==============================\n")
    
    sequence = 1000  # Starting sequence number
    
    while True:
        try:
            # Wait for a key press
            key = input("Press a button key (1/2/3/q): ")
            
            if key.lower() == 'q':
                print("Exiting button simulator...")
                break
                
            # Map key to capot type
            if key in ['1', '2', '3']:
                # Increment sequence
                sequence += 1
                seq_str = f"{sequence:04d}"
                
                # Construct message in the format expected by the application: SEQxxxxPNyWTzz
                message = f"SEQ{seq_str}PN{key}WT01"
                conn.sendall(message.encode())
                
                print(f"Button press sent: {message}")
                print(f"  - Sequence: {seq_str}")
                print(f"  - Capot type: {key}")
                
                # Wait for response from server
                try:
                    response = conn.recv(1024)
                    if response:
                        response_byte = int.from_bytes(response, byteorder='big')
                        if response_byte == 0b00000001:
                            print("Received from server: 00000001 (GOOD)")
                        elif response_byte == 0b00000010:
                            print("Received from server: 00000010 (NOGOOD)")
                        else:
                            print(f"Received unknown response: {bin(response_byte)}")
                except socket.timeout:
                    print("No response received from server")
            else:
                print("Invalid key. Use 1, 2, 3, or q.")
                
        except Exception as e:
            print(f"Error in button simulator: {str(e)}")
            if "Broken pipe" in str(e) or "Connection reset" in str(e):
                print("Connection to server lost. Exiting simulator.")
                break
            # Add a small delay before showing the menu again
            time.sleep(0.5)
    
    # Close the connection when done
    try:
        conn.close()
    except:
        pass

def handle_client(conn, addr, interval, manual_mode):
    """Handle a client connection."""
    print(f"Connected by {addr}")
    try:
        while True:
            if manual_mode:
                # In manual mode, wait for user input
                print("\nPress Enter to send a message, or type a capot type (01, 05, 08) and press Enter:")
                user_input = input()
                
                if user_input.lower() == 'exit':
                    break
                
                # Send message based on user input
                if user_input in ['01', '05', '08']:
                    send_manual_message(conn, capot_type=user_input)
                else:
                    send_manual_message(conn)
                
                # Wait for response from server
                try:
                    response = conn.recv(1024)
                    if response:
                        response_byte = int.from_bytes(response, byteorder='big')
                        if response_byte == 0b00000001:
                            print("Received from server: 00000001 (GOOD)")
                        elif response_byte == 0b00000010:
                            print("Received from server: 00000010 (NOGOOD)")
                        else:
                            print(f"Received unknown response: {bin(response_byte)}")
                except socket.timeout:
                    print("No response received from server")
            else:
                # In automatic mode, send periodic messages
                send_periodic_messages(conn, interval)
                
                # Wait for response from server
                try:
                    response = conn.recv(1024)
                    if response:
                        response_byte = int.from_bytes(response, byteorder='big')
                        if response_byte == 0b00000001:
                            print("Received from server: 00000001 (GOOD)")
                        elif response_byte == 0b00000010:
                            print("Received from server: 00000010 (NOGOOD)")
                        else:
                            print(f"Received unknown response: {bin(response_byte)}")
                except socket.timeout:
                    print("No response received from server")
                
                time.sleep(interval)
    except ConnectionResetError:
        print("Connection reset by server")
    except Exception as e:
        print(f"Error in client handler: {e}")
    finally:
        print("Closing connection")
        conn.close()

def start_fake_server(host='127.0.0.1', port=12345, interval=5, mode='auto'):
    """Start a fake PLC server that sends messages."""
    print(f"Starting fake PLC server on {host}:{port}")
    
    if mode == 'auto':
        print(f"Automatic mode: Messages will be sent every {interval} seconds")
    elif mode == 'manual':
        print("Manual mode: You will need to trigger messages manually")
    elif mode == 'button':
        print("Button simulator mode: Press keys to simulate button presses")
    
    while True:
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
                # Wait for a connection
                conn, addr = server_socket.accept()
                conn.settimeout(1.0)  # Set timeout for receiving responses
                
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
                    
                    if mode == 'button':
                        client_thread.join()

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
    parser.add_argument('--mode', choices=['auto', 'manual', 'button'], default='auto',
                        help='Operation mode: auto (periodic messages), manual (type to send), or button (simulate buttons)')
    
    args = parser.parse_args()
    
    # Start the server with the specified mode
    start_fake_server(args.host, args.port, args.interval, args.mode)
