# tests/test_scooter.py

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
from master_pi.service.ScooterService import Scooter
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal

def test_fetch_available_scooters(client):
    mocked_scooters = [
        {
            "id": 1,
            "make": "Yamaha",
            "color": "blue",
            "location": "A1",  # matches get_all_scooter's zone name alias
            "power_remaining": 85,
            "cost_per_minute": 2.5,
            "status": "available",
            "image_url": "https://example.com/scooter1.jpg"
        },
        {
            "id": 2,
            "make": "Honda",
            "color": "red",
            "location": "B2",
            "power_remaining": 40,
            "cost_per_minute": 2.0,
            "status": "unavailable",
            "image_url": "https://example.com/scooter2.jpg"
        },
        {
            "id": 3,
            "make": "Vespa",
            "color": "white",
            "location": "C3",
            "power_remaining": 92,
            "cost_per_minute": 3.0,
            "status": "available",
            "image_url": "https://example.com/scooter3.jpg"
        }
    ]

    with patch('routes.booking_routes.send_request') as mock_send, \
         patch('routes.booking_routes.update_session_balance') as mock_update_balance:

        mock_send.return_value = f"SUCCESS|{json.dumps(mocked_scooters)}"
        mock_update_balance.return_value = True

        # Setup session user_id
        with client.session_transaction() as session:
            session['user_id'] = 1
            session['role'] = 'user'

        response = client.get('/booking')
        assert response.status_code == 200

        # Only available scooters shown
        assert b"Yamaha" in response.data
        assert b"Vespa" in response.data
        assert b"Honda" not in response.data

        # Optional: check message param handled (e.g. no error)
        response_with_message = client.get('/booking?message=TestMessage')
        assert response_with_message.status_code == 200
        assert b"Yamaha" in response_with_message.data
        
def test_get_all_scooter_success():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Sample data with Decimal fields
    scooters_data = [
        {
            "id": 1,
            "make": "Yamaha",
            "color": "blue",
            "location": "ZoneA",
            "power_remaining": Decimal('85.5'),
            "cost_per_minute": Decimal('2.5'),
            "status": "available",
            "image_url": "http://example.com/scooter1.jpg"
        }
    ]

    mock_cursor.fetchall.return_value = scooters_data

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn):
        result = Scooter.get_all_scooter()

    status, payload = result.split('|', 1)
    assert status == "SUCCESS"

    data = json.loads(payload)
    assert isinstance(data, list)
    assert len(data) == 1
    scooter = data[0]

    # Check Decimal converted to float
    assert isinstance(scooter['power_remaining'], float)
    assert isinstance(scooter['cost_per_minute'], float)

    # Check other fields
    assert scooter['make'] == "Yamaha"
    assert scooter['location'] == "ZoneA"

    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

def test_get_all_scooter_not_found():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn):
        result = Scooter.get_all_scooter()

    assert result == "NOT_FOUND"
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

def test_get_all_scooter_error():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Raise exception on execute to simulate DB error
    mock_cursor.execute.side_effect = Exception("DB error")

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn):
        result = Scooter.get_all_scooter()

    assert result.startswith("ERROR|DB error")
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()

def send_request_side_effect(command):
    if command == "GET_ALL_SCOOTER":
        return "ERROR|Something broke"
    elif command.startswith("GET_BY_ID"):
        return 'SUCCESS|{"balance": 100.0}'
    else:
        return "FAIL|Unknown command"

def test_fetch_scooters_backend_failure(client):
    with patch('socket_com.send_socket.send_request', side_effect=send_request_side_effect), \
         patch('webpage.utils.session_utils.send_request', side_effect=send_request_side_effect):

        with client.session_transaction() as session:
            session['user_id'] = 1

        response = client.get('/booking')
        assert response.status_code == 500
        assert b"booking" in response.data

def test_fetch_scooters_no_available(client):
    mocked_scooters = [
        {"id": 1, "make": "Yamaha", "color": "blue", "location": "A1", "battery": 85, "cost_per_minute": 2.5, "status": "unavailable"},
    ]

    with patch('routes.booking_routes.send_request') as mock_send, \
         patch('routes.booking_routes.update_session_balance') as mock_update_balance:

        mock_send.return_value = f"SUCCESS|{json.dumps(mocked_scooters)}"
        mock_update_balance.return_value = True

        with client.session_transaction() as session:
            session['user_id'] = 1
            session['role'] = 'user'
        response = client.get('/booking')
        assert response.status_code == 200
        assert b"Yamaha" not in response.data
def test_confirm_booking_valid_scooter(client):
    mocked_scooter = {
        "id": 1,
        "make": "Yamaha",
        "color": "blue",
        "location": "A1",
        "battery": 85,
        "cost_per_minute": 2.5,
        "status": "available",
        "comments": []  # Add this key, empty list or mock comments
    }

    with patch('routes.booking_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(mocked_scooter)}"

        with client.session_transaction() as sess:
            sess['user'] = 'testuser'  # Set required session key

        response = client.get('/confirm_booking?scooter_id=1')
        assert response.status_code == 200
        assert b"Yamaha" in response.data
        assert b"A1" in response.data


def test_confirm_booking_invalid_id(client):
    with patch('routes.booking_routes.send_request') as mock_send:
        mock_send.return_value = "FAILURE|Scooter not found"

        response = client.get('/confirm_booking?scooter_id=999', follow_redirects=True)
        assert response.status_code == 200
        assert b"Invalid scooter selection" in response.data or b"booking" in response.data


def test_get_all_scooter_direct_success():
    # Mocking the get_db method to return a mock database connection
    with patch('master_pi.service.ScooterService.get_db') as mock_get_db, \
         patch('master_pi.service.ScooterService.get_all_from_table') as mock_get_all_from_table:

        # Create a mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Set up the mock for cursor and database connection
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the execution of the query and the return value
        # Returning a list of dictionaries with actual data, not MagicMock objects
        mock_cursor.fetchall.return_value = [{
            "id": 1,
            "make": "Yamaha",
            "cost_per_minute": 2.5,
            "battery": 90,
            "location": "A1",
            "status": "available",
            "color": "blue",
        }]

        # Assuming get_all_scooter is a static method or function in ScooterService
        result = Scooter.get_all_scooter()
        
        # Debugging line
        print(result)

        # Check if the result starts with "SUCCESS|"
        assert result.startswith("SUCCESS|")

        # Extract the JSON data from the result
        data = json.loads(result.split("|")[1])
        
        # Assert that the data is a list and check the first item
        assert isinstance(data, list)
        assert data[0]["make"] == "Yamaha"
        assert data[0]["status"] == "available"
        assert data[0]["color"] == "blue"
        
def test_get_scooter_by_id_success():
    mock_scooter_id = 77
    mock_data = {
        "id": mock_scooter_id,
        "status": "available",
        "latitude": Decimal("37.7749"),
        "longitude": Decimal("-122.4194")
    }

    with patch('master_pi.service.ScooterService.get_db') as mock_get_db, \
         patch('master_pi.service.ScooterService.get_by_field') as mock_get_by_field:

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_get_by_field.return_value = mock_data

        result = Scooter.get_scooter_by_id(mock_scooter_id)

        assert result.startswith("SUCCESS|")
        data = json.loads(result.split("|", 1)[1])
        assert data["id"] == mock_scooter_id
        assert isinstance(data["latitude"], float)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_scooter_by_id_not_found():
    mock_scooter_id = 88

    with patch('master_pi.service.ScooterService.get_db') as mock_get_db, \
         patch('master_pi.service.ScooterService.get_by_field') as mock_get_by_field:


        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_get_by_field.return_value = None

        result = Scooter.get_scooter_by_id(mock_scooter_id)

        assert result == "FAILURE|Scooter not found"
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_scooter_by_id_failure():
    with patch('master_pi.service.ScooterService.get_db') as mock_get_db, \
         patch('master_pi.service.ScooterService.get_by_field') as mock_get_by_field:

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_get_by_field.side_effect = Exception("Test error")

        result = Scooter.get_scooter_by_id(77)
        assert result.startswith("ERROR|Test error")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_scooter_details_success():
    scooter_id = 1

    mock_scooter = {
        "id": scooter_id,
        "make": "Yamaha",
        "zone_id": 10,
        "power_remaining": Decimal("80.5"),
        "cost_per_minute": Decimal("2.5"),
        "status": "available",
        "color": "blue",
        "image_url": "http://example.com/scooter.jpg"
    }
    mock_location = {"id": 10, "name": "ZoneA"}
    mock_comments = [
        {"id": 101, "scooter_id": scooter_id, "comment": "Good scooter", "rating": Decimal("4.5")},
        {"id": 102, "scooter_id": scooter_id, "comment": "Needs maintenance", "rating": Decimal("2.0")}
    ]

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn), \
         patch('master_pi.service.ScooterService.get_by_field') as mock_get_by_field:

        # Setup get_by_field side effects:
        # 1st call for scooter, 2nd for location, 3rd for comments
        mock_get_by_field.side_effect = [mock_scooter, mock_location, mock_comments]

        result = Scooter.get_scooter_details(scooter_id)

        status, payload = result.split('|', 1)
        assert status == "SUCCESS"

        data = json.loads(payload)

        # Assert location replaced
        assert data['location'] == mock_location['name']

        # Assert comments included and decimals converted to float
        assert isinstance(data['comments'], list)
        assert len(data['comments']) == 2
        for comment in data['comments']:
            assert isinstance(comment['rating'], float)

        # Assert scooter decimals converted to float
        assert isinstance(data['power_remaining'], float)
        assert isinstance(data['cost_per_minute'], float)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_scooter_details_not_found():
    scooter_id = 999

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn), \
         patch('master_pi.service.ScooterService.get_by_field', return_value=None):

        result = Scooter.get_scooter_details(scooter_id)
        assert result == "FAILURE|Scooter not found"

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_scooter_details_exception():
    scooter_id = 1

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('master_pi.service.ScooterService.get_db', return_value=mock_conn), \
         patch('master_pi.service.ScooterService.get_by_field', side_effect=Exception("DB failure")):

        result = Scooter.get_scooter_details(scooter_id)
        assert result.startswith("ERROR|DB failure")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()
 
def test_confirm_booking_route_success(client):
    scooter_id = 1
    scooter_data = {
        "id": scooter_id,
        "make": "Yamaha",
        "color": "blue",
        "location": "A1",
        "battery": 85,
        "cost_per_minute": 2.5,
        "status": "available",
        "comments": [
        {"id": 1, "context": "Nice scooter", "username": "user1"},
        {"id": 2, "context": "Battery good", "username": "user2"}
         ]

    }

    # Mock send_request to simulate get_scooter_details response
    with patch('routes.booking_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(scooter_data)}"

        with client.session_transaction() as sess:
            sess['user'] = 'testuser'  # required session key

        response = client.get(f'/confirm_booking?scooter_id={scooter_id}')
        assert response.status_code == 200
        assert b"Yamaha" in response.data
        assert b"A1" in response.data
        assert b"Nice scooter" in response.data

def test_confirm_booking_route_invalid_id(client):
    with patch('routes.booking_routes.send_request') as mock_send, \
         patch('routes.booking_routes.update_session_balance') as mock_update_balance:

        mock_send.return_value = "FAILURE|Scooter not found"
        mock_update_balance.return_value = True

        with client.session_transaction() as sess:
            sess['role'] = 'user'
            sess['user_id'] = 1

        response = client.get('/confirm_booking?scooter_id=999', follow_redirects=True)

        assert response.status_code == 200
        assert b"Invalid scooter selection" in response.data
