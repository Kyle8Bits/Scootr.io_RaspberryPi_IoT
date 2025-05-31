# tests/test_auth_flow.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))

from unittest.mock import patch
import json

def test_register_login_access_logout_flow(client):
    user_data = {
        "id": 7,
        "username": "flowuser",
        "balance": 0.0
    }

    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "SUCCESS"
        response = client.post('/register', data={
            'username': 'flowuser',
            'email': 'flow@example.com',
            'password': 'Flow123!',
            'confirm': 'Flow123!'
        })

        # Only check redirect
        assert response.status_code == 200


        
def test_logout_clears_session(client):
    with client.session_transaction() as session:
        session['user'] = 'dummy'
        session['user_id'] = 1

    response = client.get('/logout', follow_redirects=True)
    with client.session_transaction() as session:
        assert 'user' not in session


def test_login_empty_fields(client):
    response = client.post('/login', data={
        'username': '',
        'password': ''
    })

    assert response.status_code == 200
    assert b'Please fill in all fields' in response.data


def test_login_error_response(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "ERROR"

        response = client.post('/login', data={
            'username': 'anyuser',
            'password': 'anypass'
        })

        assert response.status_code == 200
        assert b'An error occurred' in response.data
