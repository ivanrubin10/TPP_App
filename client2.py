import socket

def start_client():
    host = '169.254.53.31'  # Dirección IP del servidor (PLC)
    port = 12345        # Número de puerto

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        print("Conectado al PLC")
        
        try:
            while True:
                # Data que recibe desde el PLC
                data = client_socket.recv(1024)
                if not data:
                    break
                print("Recibido:", data.decode())

                # Escribo mensaje para salir
                #message = input("'exit' para salir: ")
                #if message.lower() == 'exit':
                #    break
                #client_socket.sendall(message.encode())

            # Cerrar conexión
            client_socket.close()
        except Exception as e:
            print("Error: ", e)
        finally:
            print("Conexión cerrada")

start_client()