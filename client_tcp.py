#SImple TCP client to test connectivity

import socket

HOST = '34.154.94.220'  # The server's hostname or IP address
#HOST='34.154.94.220'
PORT = 55555      # The port used by the server
CLIENT_PORT = 30002 # The port used by the client

# Create a socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    # Bind the socket to a specific address and port
    s.bind(("0.0.0.0", CLIENT_PORT))

    # Connect to the server
    s.connect((HOST, PORT))

    # Receive the response from the server
    data = s.recv(1024)

print('Received:', data.decode())