import socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.137.152', 5000))  # Replace with actual RPi IP
print("Connected to server")
client_socket.close()
