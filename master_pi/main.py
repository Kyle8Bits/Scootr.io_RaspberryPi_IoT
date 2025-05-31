"""
main.py

Entry point of the scooter management server.

This module initializes and starts the server by calling the server setup function
defined in the MP_init module.
"""

import sys
import os
from .MP_init import init_server



if __name__ == "__main__":
    init_server()
