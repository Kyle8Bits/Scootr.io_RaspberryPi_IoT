import socket

MP_address = ("192.168.0.128", 3333)

def send_request(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(MP_address)  # MP is running on localhost with port 3333
        s.sendall(data.encode('utf-8'))  # Send login data
        
        # Initialize an empty response
        response = ""
        buffer_size = 8192  # Chunk size used for receiving
        total_received = 0  # Track the total number of bytes received
        
        while True:
            chunk = s.recv(buffer_size).decode('utf-8')  # Receive up to 8192 bytes at a time
            if not chunk:  # No more data to receive
                break
            response += chunk
            total_received += len(chunk)
        
        return response