import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from flask import session
from urllib.parse import urlparse, parse_qs

# Setup sys.path as before
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'master_pi'))

from master_pi.service.UserService import User

def login_test_user(client, username='testuser'):
    with client.session_transaction() as sess:
        sess['user'] = username


@patch('routes.booking_routes.send_request')
def test_add_comment_success_redirects(mock_send, client):
    # Arrange
    mock_send.return_value = "SUCCESS|Comment added"
    with client.session_transaction() as sess:
        sess['user'] = 'testuser'

    # Act
    response = client.post('/confirm_booking?scooter_id=123', data={'comment': 'Nice scooter'})

    # Assert
    assert response.status_code == 302
    assert "/booking?message=%E2%9C%85+Comment+added+successfully!" in response.location


@patch('routes.booking_routes.send_request')
def test_add_comment_failure_redirects(mock_send, client):
    mock_send.return_value = "ERROR|Failed"
    with client.session_transaction() as sess:
        sess['user'] = 'testuser'

    response = client.post('/confirm_booking?scooter_id=123', data={'comment': 'Nice scooter'})

    assert response.status_code == 302
    assert "/booking?message=%E2%9D%8C+Failed+to+add+comment." in response.location


def test_add_comment_missing_data_redirects(client):
    with client.session_transaction() as sess:
        sess['user'] = 'testuser'

    response = client.post('/confirm_booking?scooter_id=123', data={'comment': ''})
    assert response.status_code == 302
    assert "/booking?message=%E2%9D%8C+Failed+to+add+comment." in response.location
    
@patch('master_pi.service.UserService.get_db')
def test_create_comment_success(mock_get_db):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.return_value = None
    mock_conn.commit.return_value = None

    result = User.create_comment('testuser', '123', 'Nice scooter')

    mock_cursor.execute.assert_called_once_with(
        """
                INSERT INTO comments (username, scooter_id, context)
                VALUES (%s, %s, %s)
            """,
        ('testuser', '123', 'Nice scooter')
    )
    mock_conn.commit.assert_called_once()
    assert result == "SUCCESS"

@patch('master_pi.service.UserService.get_db')
def test_create_comment_failure(mock_get_db):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_get_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.side_effect = Exception("DB Error")

    result = User.create_comment('testuser', '123', 'Nice scooter')

    assert result.startswith("ERROR|")

@patch('webpage.routes.booking_routes.send_request')
def test_add_comment_missing_data(mock_send_request, client):
    login_test_user(client, 'testuser')

    response = client.post('/confirm_booking', data={'comment': ''})

    assert response.status_code == 302
    location = response.headers['Location']
    parsed_url = urlparse(location)
    query_params = parse_qs(parsed_url.query)
    assert parsed_url.path.endswith('/booking')
    assert query_params.get('message') == ["❌ Failed to add comment."]