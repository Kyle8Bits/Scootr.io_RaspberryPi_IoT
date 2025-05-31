# tests/test_crud.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
from unittest.mock import patch, MagicMock
from master_pi.service.crud import get_by_field, update_field, add_into_table, get_all_from_table
from master_pi.service.ScooterService import Scooter

def test_get_all_from_table_success():
    # Mock the data returned from the database
    mock_scooter_data = [
        {"id": 1, "location": "Park A", "status": "available"},
        {"id": 2, "location": "Park B", "status": "in-use"}
    ]

    with patch('master_pi.service.ScooterService.get_db') as mock_db:
        # Create a mock database cursor
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor

        # Mock the result of fetchall to return mock_scooter_data
        mock_cursor.fetchall.return_value = mock_scooter_data
        mock_cursor.execute.return_value = None  # Simulate that the execute method doesn't return anything

        # Call the function under test
        result = get_all_from_table(mock_cursor, "scooters")

        # Assertions
        assert result == mock_scooter_data  # Check that the result matches the mock data
        mock_cursor.execute.assert_called_once_with("SELECT * FROM scooters")  # Ensure the correct SQL query was executed

def test_add_into_table_success():
    # Mock the data to be inserted
    mock_data = {
        "username": "john_doe",
        "email": "john@example.com"
    }

    with patch('master_pi.service.UserService.get_db') as mock_db:
        # Create a mock database cursor
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor

        # Call the function under test
        result = add_into_table(mock_cursor, "users", mock_data)

        # Assertions
        assert result == "SUCCESS"  # Ensure the function returns "SUCCESS"
        # Ensure the correct SQL query was executed
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO users (username, email) VALUES (%s, %s)", 
            ('john_doe', 'john@example.com')
        )


def test_add_into_table_error():
    # Simulate a database error
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        # Call the function under test
        result = add_into_table(mock_cursor, "users", {"username": "john_doe", "email": "john@example.com"})

        # Assertions
        assert result.startswith("ERROR")  # Ensure the result starts with "ERROR"
        assert "Database error" in result  # Ensure the error message is included
