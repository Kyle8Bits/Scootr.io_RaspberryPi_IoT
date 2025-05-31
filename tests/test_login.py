# tests/test_login.py

import sys
import os
import json
from unittest.mock import patch

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))


def test_login_successful_user_redirect(client):
    user_data = {
        "id": 1,
        "username": "testuser",
        "balance": 100.0,
        "role": "customer"
    }

    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(user_data)}"
        response = client.post('/login', data={'username': 'testuser', 'password': 'correctpass'})

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/booking')


def test_login_successful_admin_redirect(client):
    user_data = {
        "id": 2,
        "username": "adminuser",
        "balance": 100.0,
        "role": "admin"
    }

    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(user_data)}"
        response = client.post('/login', data={'username': 'adminuser', 'password': 'adminpass'})

        assert response.status_code == 302
        assert '/admin/home' in response.headers['Location']


def test_login_successful_engineer_redirect(client):
    user_data = {
        "id": 3,
        "username": "engineeruser",
        "balance": 100.0,
        "role": "engineer"
    }

    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(user_data)}"
        response = client.post('/login', data={'username': 'engineeruser', 'password': 'engineerpass'})

        assert response.status_code == 302
        assert '/engineer/engineer_home' in response.headers['Location']


def test_login_invalid_password(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "FAILURE|Invalid credentials"

        response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'})

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data


def test_login_nonexistent_user(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "NOT_FOUND|User not found"

        response = client.post('/login', data={'username': 'ghostuser', 'password': 'somepass'})

        assert response.status_code == 200
        assert b'Cannot find your account' in response.data


def test_login_error_response(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "ERROR|Something went wrong"

        response = client.post('/login', data={'username': 'erroruser', 'password': 'errorpass'})

        assert response.status_code == 200
        assert b'An error occurred' in response.data


def test_login_missing_fields(client):
    response = client.post('/login', data={'username': '', 'password': ''})
    assert response.status_code == 200
    assert b'Please fill in all fields' in response.data


def test_login_session_created(client):
    user_data = {
        "id": 4,
        "username": "sessionuser",
        "balance": 400.0,
        "role": "customer"
    }

    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(user_data)}"

        with client.session_transaction() as session:
            assert 'user' not in session

        client.post('/login', data={'username': 'sessionuser', 'password': 'pass123'})

        with client.session_transaction() as session:
            assert session['user'] == 'sessionuser'
            assert session['user_id'] == 4
            assert session['balance'] == 400.0
            assert session['role'] == 'customer'
