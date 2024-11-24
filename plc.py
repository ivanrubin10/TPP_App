import socket
import time
import threading
import random

def send_periodic_messages(conn):
    # Function to send periodic messages to the client
    while True:
        time.sleep(30)  # Send a message every x seconds
        message = str(random.choice(['01', '05', '08']))
        conn.sendall(message.encode())
        print(f"Sent: {message}")

def start_fake_server():
    host = '127.0.0.1'  # Use localhost for testing
    port = 12345         # Port number

    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the IP and port
        server_socket.bind((host, port))
        
        # Start listening for incoming connections
        server_socket.listen(1)
        print(f"Fake server listening on {host}:{port}")

        # Wait for a connection
        conn, addr = server_socket.accept()
        with conn:
            print(f"Connected by {addr}")
            
            # Start a separate thread to send periodic messages
            threading.Thread(target=send_periodic_messages, args=(conn,), daemon=True).start()
            
            # Receive and handle messages from the client
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Received from client: {data.decode()}")

                # Send a response to the client
                response = "Message received!"
                conn.sendall(response.encode())

if __name__ == '__main__':
    start_fake_server()
