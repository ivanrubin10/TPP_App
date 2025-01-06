import socket
import time
import threading
import random

def send_periodic_messages(conn):
    # Function to send periodic messages to the client
    while True:
        try:
            time.sleep(30)  # Send a message every x seconds
            message = str(random.choice(['01', '05', '08']))
            conn.sendall(message.encode())
            print(f"Sent: {message}")
            
        except:
            break

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    
    # Start a separate thread to send periodic messages
    message_thread = threading.Thread(target=send_periodic_messages, args=(conn,), daemon=True)
    message_thread.start()
    
    # Receive and handle messages from the client
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"Received from client: {data.decode()}")

            # Send a response to the client
            response = "Message received!"
            conn.sendall(response.encode())
    except:
        pass
    finally:
        conn.close()

def start_fake_server():
    host = '127.0.0.1'  # Use localhost for testing
    port = 12345         # Port number

    while True:
        try:
            # Create a socket object
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Bind the socket to the IP and port
            server_socket.bind((host, port))
            
            # Start listening for incoming connections
            server_socket.listen(1)
            print(f"Fake server listening on {host}:{port}")

            while True:
                # Wait for a connection
                conn, addr = server_socket.accept()
                # Handle client in a separate thread
                client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                client_thread.start()

        except Exception as e:
            print(f"Server error: {e}")
            print("Restarting server in 5 seconds...")
            time.sleep(5)
        finally:
            server_socket.close()

if __name__ == '__main__':
    start_fake_server()
