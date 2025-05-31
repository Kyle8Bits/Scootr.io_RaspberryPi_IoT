# db/__init__.py

import mysql.connector

def get_db():
    return mysql.connector.connect(
        host='34.142.244.18',
        user='thao',
        password='thao',
        database='iot-assignment2'
    )
