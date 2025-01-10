import socket
import time
import threading
import random

# Global variable to track the active connection
active_connection = None

def create_galc_message(empty=False):
    message = bytearray(45)
    # Header details (as specified in the original file)
    message[0:6] = b"LSA270"  # Receiver logical name
    message[6:12] = b"OUTP_P"  # Sender logical name
    message[12:16] = b"0000"  # Serial number
    message[16:22] = b"00019 "  # Mode + Data length
    message[22:24] = b"00"  # Process type
    message[24:26] = b"  "  # Process result
    message[26:27] = b"1"  # Line
    message[27:29] = b"Q0"  # Tracking point

    # Sequence number handling
    if not hasattr(create_galc_message, 'sequence_num'):
        create_galc_message.sequence_num = 601
    seq = str(create_galc_message.sequence_num).zfill(3)
    create_galc_message.sequence_num = (create_galc_message.sequence_num + 1) % 1000
    message[29:32] = seq.encode()

    if not empty:
        # Generate random body and status bytes
        body_num = f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000, 9999)}"
        model_num = f"{random.randint(0, 999):03d}"
        random_val = random.choice([1, 5, 8])  # Possible triggers for Vue.js
        message[32:37] = body_num.encode()
        message[37:40] = model_num.encode()
        message[40:43] = b"000"  # Placeholder
        message[43:45] = bytes([0, random_val])
    else:
        # Zero out the body if empty
        message[32:45] = bytes([0] * 13)

    return message


def handle_client(conn, addr):
    global active_connection
    if active_connection is not None:
        print(f"Connection attempt from {addr} rejected. Already connected to {active_connection}.")
        conn.close()  # Reject the new connection
        return
    
    active_connection = addr  # Set the active connection
    print(f"New client connected from {addr}")
    stop_signal_received = False

    try:
        while not stop_signal_received:
            # Send a 45-byte GALC message
            message = create_galc_message(empty=False)
            conn.sendall(message)
            readable_message = f"Receiver: {message[0:6].decode()}, Sender: {message[6:12].decode()}, Serial: {message[12:16].decode()}, Trigger: {message[44]:02d}"
            print(f"Sent GALC message: {readable_message}")

            # Expect a 26-byte response from the client
            data = conn.recv(26)
            if len(data) != 26:
                print(f"Invalid response length: {len(data)}. Closing connection.")
                break

            print(f"Received client response: Terminal: {data[0:6].decode()}, Sender: {data[6:12].decode()}, Serial: {data[12:16].decode()}, Status: {data[25]}")

            # Process the 26-byte response
            if data[25] == 1:  # Stop signal received
                print("Stop signal received. Sending zero-filled message.")
                zero_message = create_galc_message(empty=True)
                conn.sendall(zero_message)
                # stop_signal_received = True
            else:
                print("Keep-alive response received. Continuing communication.")

            time.sleep(15)  # Wait before sending the next message
    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        conn.close()
        print(f"Connection with {addr} closed.")
        active_connection = None  # Reset the active connection


def start_fake_server():
    host = "127.0.0.1"
    port = 54321

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"GALC server is running and listening on {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start_fake_server()
