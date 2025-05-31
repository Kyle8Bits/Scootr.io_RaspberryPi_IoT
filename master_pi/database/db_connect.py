"""
db_connect.py

Database connection module for the scooter management system.

This module uses environment variables loaded via dotenv to establish a connection
to a MySQL database. It provides a reusable connection function for all service modules.

Environment variables required:
- DB_IP: The IP address of the database server
- DB_USER: The MySQL username
- DB_PASS: The MySQL password
- DB_NAME: The name of the database
"""

import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def db_connect():
    """
    Establish a connection to the MySQL database using environment variables.

    Returns:
        mysql.connector.connection.MySQLConnection: A live connection object if successful.
        None: If the connection fails.
    """
    try:
        db_connection = mysql.connector.connect(
            host=os.getenv("DB_IP"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME")
        )

        print("Connected to the database successfully!")
        return db_connection
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
