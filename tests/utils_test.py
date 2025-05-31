from unittest.mock import patch
import json
import pytest
from flask import session
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from webpage.utils.session_utils import update_session_balance

@pytest.fixture
def app_with_context(app):
    with app.app_context():
        yield app

@patch('webpage.utils.session_utils.send_request')
def test_update_session_balance_success(mock_send, app_with_context, client):
    user_id = 1
    user_data = {"balance": 50.75}
    mock_send.return_value = f"SUCCESS|{json.dumps(user_data)}"

    with client.application.test_request_context():
        # Call the function which modifies session inside request context
        result = update_session_balance(user_id)
        from flask import session
        assert result is True
        assert abs(session['balance'] - user_data['balance']) < 1e-6



@patch('webpage.utils.session_utils.send_request')
def test_update_session_balance_failure(mock_send, app_with_context, client):
    mock_send.return_value = "FAILURE|User not found"
    user_id = 999

    with client.application.test_request_context():
        result = update_session_balance(user_id)
        from flask import session
        assert result is False
        assert 'balance' not in session
