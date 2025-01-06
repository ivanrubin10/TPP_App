import socket
import time
import threading
import random

def create_galc_message():
    # Create 45 byte message
    message = bytearray(45)
    
    # Bytes 1-6: Receiver logical name
    message[0:6] = 'LSA270'.encode()
    
    # Bytes 7-12: Sender logical name  
    message[6:12] = 'OUTP_P'.encode()
    
    # Bytes 13-16: Serial number
    message[12:16] = '0000'.encode()
    
    # Byte 17: Mode
    message[16] = 1
    
    # Bytes 18-22: Data length 
    message[17:22] = '00019'.encode()
    
    # Bytes 23-24: Process type
    message[22:24] = '00'.encode()
    
    # Bytes 25-26: Process result
    message[24:26] = '  '.encode()
    
    # Byte 27: Line
    message[26] = 1
    
    # Bytes 28-29: Tracking point
    message[27:29] = 'Q0'.encode()
    
    # Generate sequence number (incrementing)
    global sequence_num
    if not hasattr(create_galc_message, 'sequence_num'):
        create_galc_message.sequence_num = 601
    seq = str(create_galc_message.sequence_num).zfill(3)
    message[29:32] = seq.encode()
    create_galc_message.sequence_num = (create_galc_message.sequence_num + 1) % 1000
    
    # Generate random body number (5 chars)
    body_num = f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1000,9999)}"
    message[32:37] = body_num.encode()
    
    # Generate random model number (3 digits)
    model_num = f"{random.randint(0,999):03d}"
    message[37:40] = model_num.encode()
    
    # Bytes 41-43: Other vehicle info
    message[40:43] = '000'.encode()
    
    # Last two bytes: random value from [1,5,8]
    random_val = random.choice([1,5,8])
    message[43:45] = bytes([0, random_val])
    
    print(f"Created GALC message: {message.decode('ascii', errors='replace')}")
    return message

def send_periodic_messages(conn, last_response_time, last_response_status):
    # Initialize thread local values
    last_response_time.value = time.time()
    last_response_status.value = '00'
    
    # Wait 10 seconds before sending the first message
    time.sleep(10)
    
    while True:
        try:
            current_time = time.time()
            if current_time - last_response_time.value > 60:
                print("No response from client for 30 seconds, closing connection")
                try:
                    conn.close()
                except:
                    pass
                return

            # Only send if we've received a response (status 00 or 01) 
            if last_response_status.value in ['00', '01']:
                try:
                    message = create_galc_message()
                    # If last response had status 1, send empty data
                    if last_response_status.value == '01':
                        # Zero out all data fields but keep header info
                        message[32:45] = bytes([0] * 13)
                        print("Sending empty data message")
                    try:
                        conn.sendall(message)
                        print(f"Sent GALC message: {message.decode('ascii', errors='replace')} ({len(message)} bytes)")
                    except socket.error:
                        print("Socket error while sending message")
                        return
                except Exception as e:
                    print(f"Error creating/sending message: {str(e)}")
                    try:
                        conn.close()
                    except:
                        pass
                    return
            
            time.sleep(15)  # Send messages every 15 seconds
            
        except Exception as e:
            print(f"Error in send_periodic_messages: {str(e)}")
            try:
                conn.close()
            except:
                pass
            return

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    
    # Use mutable objects to share state between threads
    last_response_time = threading.local()
    last_response_time.value = time.time()
    
    last_response_status = threading.local() 
    last_response_status.value = '00'  # Default status
    
    # Store last sent message details for verification
    last_sent_msg = threading.local()
    last_sent_msg.terminal = None
    last_sent_msg.sender = None
    last_sent_msg.serial = None
    
    # Start a separate thread to send periodic messages
    message_thread = threading.Thread(
        target=send_periodic_messages, 
        args=(conn, last_response_time, last_response_status),
        daemon=True
    )
    message_thread.start()
    
    # Receive and handle messages from the client
    try:
        while True:
            try:
                data = conn.recv(26)  # Expect 26 byte response
                if not data:
                    print("Client disconnected")
                    break
                    
                print(f"Received raw data from client: {data.decode('ascii', errors='replace')}")
                    
                # Parse 26 byte response
                try:
                    terminal_name = data[0:6]
                    sender_name = data[6:12] 
                    serial_number = data[12:16]
                    # Bytes 17-25 are zeros
                    response_status = data[25]  # 0 for first message, 1 for subsequent
                except IndexError:
                    print(f"Error: Received malformed data of length {len(data)}")
                    continue
                    
                # Verify the response matches the sent message
                if (last_sent_msg.terminal and last_sent_msg.sender and last_sent_msg.serial):
                    if (terminal_name.decode() != last_sent_msg.sender.decode() or  # Terminal should match sender from our msg
                        sender_name.decode() != last_sent_msg.terminal.decode() or  # Sender should match terminal from our msg
                        serial_number.decode() != last_sent_msg.serial.decode()):   # Serial should match
                        print("Warning: Response fields don't match sent message!")
                        print(f"Expected: Terminal={last_sent_msg.sender.decode()}, Sender={last_sent_msg.terminal.decode()}, Serial={last_sent_msg.serial.decode()}")
                        print(f"Received: Terminal={terminal_name.decode()}, Sender={sender_name.decode()}, Serial={serial_number.decode()}")
                
                # Store details of sent message for next verification
                # Wait for client response before creating a new message
                # msg = create_galc_message()
                # last_sent_msg.terminal = msg[0:6]  # Receiver name becomes client's sender
                # last_sent_msg.sender = msg[6:12]   # Sender name becomes client's terminal
                # last_sent_msg.serial = msg[12:16]  # Serial number should match
                
                print(f"Received from client: Terminal={terminal_name.decode()}, Sender={sender_name.decode()}, "
                      f"Serial={serial_number.decode()}, Status={response_status}")
                
                # Update last response time and status
                last_response_time.value = time.time()
                last_response_status.value = str(response_status)
            except (socket.error, ConnectionResetError) as e:
                print(f"Socket error while receiving data: {str(e)}")
                break
            
    except Exception as e:
        print(f"Error in handle_client: {str(e)}")
    finally:
        print("Closing client connection")
        try:
            conn.close()
        except:
            pass

def start_fake_server():
    host = '127.0.0.1'  # Use localhost for testing
    port = 54321        # Port number

    while True:
        server_socket = None
        try:
            # Create a socket object
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Bind the socket to the IP and port
            server_socket.bind((host, port))
            
            # Start listening for incoming connections
            server_socket.listen(1)
            print(f"Fake server listening on {host}:{port}")

            while True:
                # Wait for a connection
                conn, addr = server_socket.accept()
                print(f"New client connection from {addr}")
                # Handle client in a separate thread
                client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                client_thread.start()

        except Exception as e:
            print(f"Server error: {str(e)}")
            print("Restarting server in 5 seconds...")
            time.sleep(5)
        finally:
            if server_socket:
                try:
                    print("Closing server socket")
                    server_socket.close()
                except:
                    pass

if __name__ == '__main__':
    start_fake_server()
