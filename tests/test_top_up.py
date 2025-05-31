import sys
import os
import pytest
from unittest.mock import call, patch, MagicMock

# Adjust Python path to find modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))

from master_pi.service.UserService import User

# -------------------
# Test cases
# -------------------

def test_top_up_positive_amount_success():
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        result = User.top_up(user_id=1, amount=100)
        assert result.startswith("SUCCESS")

def test_top_up_rejects_negative_amount():
    result_negative = User.top_up(user_id=1, amount=-50)
    result_zero = User.top_up(user_id=1, amount=0)

    assert result_negative.startswith("FAILURE")
    assert result_zero.startswith("FAILURE")

def test_top_up_updates_user_balance():
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1

        result = User.top_up(user_id=1, amount=50)

        assert result.startswith("SUCCESS")
        mock_cursor.execute.assert_has_calls([
            call("UPDATE users SET balance = balance + %s WHERE id = %s", (50, 1)),
            call("INSERT INTO topups (user_id, amount) VALUES (%s, %s)", (1, 50)),
        ])

def test_top_up_invalid_user_id():
    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 0  # No rows updated

        result = User.top_up(user_id=9999, amount=50)

        assert result.startswith("FAILURE")

def test_top_up_handles_database_error():
    with patch('master_pi.service.UserService.get_db', side_effect=Exception("Database error")):
        result = User.top_up(user_id=1, amount=50)
        assert result.startswith("FAILURE")
