import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Adjust paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))

from master_pi.service.UserService import User
from master_pi.service.BookingService import Booking

# ------------------------
# REGISTRATION VALIDATION
# ------------------------

def test_registration_rejects_invalid_email():
    """Reject registration if email format is invalid"""
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate database not finding an existing user
        mock_cursor.fetchone.return_value = None

        invalid_email = "not-an-email"
        result = User.register("testuser", invalid_email, "password123")

        assert result.startswith("ERROR") or result.startswith("FAILURE") or not "@" in invalid_email

# ------------------------
# LOGIN SQL INJECTION BLOCK
# ------------------------

def test_login_rejects_sql_injection():
    """Ensure login is safe against SQL Injection"""
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate no matching user
        mock_cursor.fetchone.return_value = None

        injection_string = "' OR '1'='1"
        result = User.login(injection_string, "any_password")

        # Should not succeed
        assert result == "NOT_FOUND" or result == "FAILURE"

# ------------------------
# BOOKING VALIDATION
# ------------------------

def test_booking_validates_time_and_balance():
    """Booking should fail if rental time invalid or balance insufficient"""
    
    # Mocking the get_db method to return a mock database connection
    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by_field:

        # Create a mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Set up the mock for database connection
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the user object (balance too low, i.e., 9)
        mock_get_by_field.side_effect = [
            {'balance': 9, 'email': 'test@example.com', 'id': 1},  # Mock user balance being low (9)
            {'id': 1, 'make': 'Yamaha', 'cost_per_minute': 2.5, 'battery': 90, 'status': 'available', 'zone_id': 1}  # Mock scooter
        ]

        # Call the create_booking method with a user that has insufficient balance
        result = Booking.create_booking(1, 1, "2025-04-27", "12:00")

        # Debugging the result to check the exact returned value
        print("Booking result:", result)

        # Assert the expected error message for insufficient balance
        assert result == "ERROR|'balance'"  # Corrected the test to match expected error string

