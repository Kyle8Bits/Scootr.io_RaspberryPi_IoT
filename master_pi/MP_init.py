"""
MP_init.py

Server initialization module for the scooter management system.

This module sets up a TCP socket server that listens for incoming client connections.
It accepts connections and delegates client communication to the handle_client function.
"""

import socket
from .client_handle.client_handle import handle_client


# Client IP and port (server's IP and port)
server_ip = "0.0.0.0"  # Change to your server's IP address if needed
server_port = 3333

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

def init_server():
    """
    Initialize and run the server socket.

    Binds the server to a specified IP address and port, listens for incoming TCP connections,
    and processes each client using the handle_client function. 
    Handles socket and general exceptions gracefully.
    """
    # Bind the server to the IP and port
    server_socket.bind((server_ip, server_port))  
    server_socket.listen(1)  # Listen for incoming connections
    
    print(f"Master Pi (MP) is listening for connections on {server_ip}:{server_port}...")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
    
            handle_client(client_socket)

            # Close the client connection after handling
            client_socket.close()

    except socket.error as e:
        print(f"Socket error occurred: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        server_socket.close()
