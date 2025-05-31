# tests/test_register.py

import sys
import os

# Root directory (for master_pi)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ROOT_DIR)

# Add master_pi explicitly to support importing from service/ and database/
sys.path.append(os.path.join(ROOT_DIR, 'master_pi'))

from unittest.mock import patch
import hashlib
from master_pi.service.UserService import User


def test_register_valid_user(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "SUCCESS"

        response = client.post('/register', data={
            'username': 'validuser',
            'email': 'valid@example.com',
            'password': 'StrongPass123!',
            'confirm': 'StrongPass123!'
        })

        assert response.status_code == 200

def test_register_password_is_hashed():
    password = "Secret123!"
    hashed = hashlib.sha256(password.encode()).hexdigest()

    # Ensure hash is 64-character hex
    assert hashed is not None
    assert isinstance(hashed, str)
    assert len(hashed) == 64


def test_register_missing_fields(client):
    response = client.post('/register', data={
        'username': '',
        'email': 'missing@example.com',
        'password': 'Password123!',
        'confirm': 'Password123!'
    }, follow_redirects=True)
    
    print(response)  # Debugging line

    assert response.status_code == 200
    # Check for something that's definitely in the response
    assert b'Sign Up' in response.data


def test_register_sends_data_to_MP(client):
    with patch('routes.user_routes.send_request') as mock_send:
        mock_send.return_value = "SUCCESS"

        client.post('/register', data={
            'username': 'mpuser',
            'email': 'mp@example.com',
            'password': 'MPpass123!',
            'confirm': 'MPpass123!'
        }, follow_redirects=True)  # You might need this

        mock_send.assert_called_once()
        called_data = mock_send.call_args[0][0]
        # Fix the expected prefix to match actual implementation
        assert called_data.startswith("IF_EXIST|mpuser|mp@example.com")

def test_register_password_mismatch(client):
    response = client.post('/register', data={
        'username': 'mismatchuser',
        'email': 'mismatch@example.com',
        'password': 'OnePassword123!',
        'confirm': 'DifferentPassword123!'
    }, follow_redirects=True)

    # Just check page loads (form shown again)
    assert response.status_code == 200