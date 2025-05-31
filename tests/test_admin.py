# tests/test_admin_routes.py

import pytest
import sys
import os

from routes.admin_routes import safe_unpack
# from master_pi.service.AdminService import Admin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webpage')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
from utils.session_utils import mail
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal


def login_as_admin(client):
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        
def test_safe_unpack():
    assert safe_unpack("SUCCESS|payload") == ("SUCCESS", "payload")
    assert safe_unpack("SUCCESS") == ("SUCCESS", "")

@patch('routes.admin_routes.send_request')
def test_admin_home_redirect_if_not_admin(mock_send, client):
    response = client.get('/admin/home')
    assert response.status_code == 302  # redirected

@patch('routes.admin_routes.send_request')
def test_admin_home_access(mock_send, client):
    login_as_admin(client)
    response = client.get('/admin/home')
    assert response.status_code == 200
    assert b"Scootr.io Admin" in response.data

@patch('routes.admin_routes.send_request')
def test_admin_analytics_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|{"some": "data"}'
    response = client.get('/admin/analytics?view=daily')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "some" in data

@patch('routes.admin_routes.send_request')
def test_admin_analytics_failure(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'FAILURE|error message'
    response = client.get('/admin/analytics?view=daily')
    assert response.status_code == 500
    assert b"Analytics fetch failed" in response.data

@patch('routes.admin_routes.send_request')
def test_admin_metrics_success(mock_send, client):
    login_as_admin(client)
    mock_send.side_effect = ['SUCCESS|[{"id":1}]', 'SUCCESS|[{"id":2}]']  # users, scooters
    response = client.get('/admin/metrics')
    assert response.status_code == 200
    data = json.loads(response.data)
    print(data)
    assert data['customers'] != "ERROR"
    assert data['scooters'] != "ERROR"

@patch('routes.admin_routes.send_request')
def test_top_scooters_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|[{"scooter_id":1,"rides":10},{"scooter_id":2,"rides":5}]'
    response = client.get('/admin/top_scooters')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "labels" in data and "values" in data
    assert "Scooter #1" in data["labels"][0]

# Helper to simulate user NOT being admin
def login_as_user(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'

def test_admin_analytics_forbidden(client):
    login_as_user(client)
    response = client.get('/admin/analytics?view=daily')
    assert response.status_code == 403
    assert b"Forbidden" in response.data

@patch('routes.admin_routes.send_request')
def test_admin_metrics_server_error(mock_send, client):
    with patch('routes.admin_routes.send_request', side_effect=Exception("DB crashed")):
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
        response = client.get('/admin/metrics')
        assert response.status_code == 500
        assert b"DB crashed" in response.data

@patch('routes.admin_routes.send_request')
def test_top_scooters_server_error(mock_send, client):
    with patch('routes.admin_routes.send_request', side_effect=Exception("socket timeout")):
        with client.session_transaction() as sess:
            sess['role'] = 'admin'
        response = client.get('/admin/top_scooters')
        assert response.status_code == 500
        assert b"socket timeout" in response.data

def test_top_scooters_forbidden(client):
    login_as_user(client)
    response = client.get('/admin/top_scooters')
    assert response.status_code == 403
    assert b"Forbidden" in response.data

# --- Test: Successful bookings fetch ---
@patch('routes.admin_routes.send_request')
def test_usage_history_success(mock_send, client):
    login_as_admin(client)

    mocked_bookings = [
        {"id": 1, "user_id": 101, "scooter_id": 501, "start_time": "2024-01-01 10:00:00"},
        {"id": 2, "user_id": 102, "scooter_id": 502, "start_time": "2024-01-02 11:00:00"}
    ]
    mock_send.return_value = f"SUCCESS|{json.dumps(mocked_bookings)}"

    response = client.get('/admin/usage_history')
    assert response.status_code == 200
    assert b"bookings" in response.data or b"Booking" in response.data


# --- Test: Failed fetch returns empty list ---
@patch('routes.admin_routes.send_request')
def test_usage_history_failure(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Unable to fetch"

    response = client.get('/admin/usage_history')
    assert response.status_code == 200
    assert b"bookings" in response.data or b"Booking" in response.data


# --- Test: Malformed response causes exception ---
@patch('routes.admin_routes.send_request')
def test_usage_history_exception(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "MALFORMED_RESPONSE"

    response = client.get('/admin/usage_history')
    assert response.status_code == 200
    assert b"bookings" in response.data or b"Booking" in response.data

# --- Issue page render ---
def test_admin_issues_page_access(client):
    login_as_admin(client)
    response = client.get('/admin/issues')
    assert response.status_code == 200
    assert b"Issues" in response.data

# --- API Success ---
@patch('routes.admin_routes.send_request')
def test_admin_issues_api_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|[{"id":1,"status":"reported"}]'
    response = client.get('/admin/issues/api')
    assert response.status_code == 200
    assert response.json[0]['id'] == 1

# --- API Failure ---
@patch('routes.admin_routes.send_request')
def test_admin_issues_api_failure(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'FAILURE|Error'
    response = client.get('/admin/issues/api')
    assert response.status_code == 500

# --- Approve: full success ---
@patch('routes.admin_routes.mail.send')
@patch('routes.admin_routes.send_request')
def test_approve_issue_full_success(mock_send, mock_mail, client):
    login_as_admin(client)

    issue = {
        "id": 1,
        "scooter_id": 101,
        "reported_at": "2025-05-01",
        "status": "approved",
        "issue_type": "Battery",
        "additional_details": "Low battery",
        "latitude": 10.0,
        "longitude": 20.0
    }
    mock_send.side_effect = [
        "SUCCESS|Approved",  # approve
        f"SUCCESS|{json.dumps(issue)}",  # issue fetch
        f"SUCCESS|[\"eng1@mail.com\"]"  # emails
    ]

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    assert response.json['success'] is True

# --- Approve: approval fails ---
@patch('routes.admin_routes.send_request')
def test_approve_issue_approval_fail(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Nope"

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    assert response.json['success'] is False

# --- Approve: issue fetch fails ---
@patch('routes.admin_routes.send_request')
def test_approve_issue_issue_fetch_fail(mock_send, client):
    login_as_admin(client)
    mock_send.side_effect = ["SUCCESS|Approved", "FAILURE|Not found"]

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    assert response.json['success'] is False

# --- Approve: email fetch fails ---
@patch('routes.admin_routes.send_request')
def test_approve_issue_email_fetch_fail(mock_send, client):
    login_as_admin(client)
    mock_send.side_effect = [
        "SUCCESS|Approved",
        "SUCCESS|{}",  # issue fetch
        "FAILURE|No emails"
    ]

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    assert response.json['success'] is False

# --- Approve: mail send exception ---
@patch('routes.admin_routes.mail.send', side_effect=Exception("Mail error"))
@patch('routes.admin_routes.send_request')
def test_approve_issue_mail_exception(mock_send, mock_mail, client):
    login_as_admin(client)
    mock_send.side_effect = [
        "SUCCESS|Approved",
        "SUCCESS|{}",
        "SUCCESS|[\"eng@mail.com\"]"
    ]

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    assert response.json['success'] is True
    
@pytest.mark.skip(reason="Skipping mail send test due to mocking limitation.")
@patch('routes.admin_routes.mail.send')
@patch('routes.admin_routes.send_request')
def test_approve_issue_mail_success(mock_send_request, mock_mail_send, client):
    login_as_admin(client)

    mock_send_request.side_effect = [
        "SUCCESS|Approved",
        "SUCCESS|" + json.dumps({
            "id": 1,
            "scooter_id": 5,
            "reported_at": "2024-01-01",
            "status": "approved",
            "issue_type": "Battery",
            "additional_details": "",
            "latitude": 0,
            "longitude": 0
        }),
        'SUCCESS|["eng@mail.com"]'
    ]

    response = client.post('/admin/issues/approve/1')
    assert response.status_code == 200
    mock_mail_send.assert_called_once()
    
# --- GET /admin/topups ---
def test_admin_topups_page(client):
    login_as_admin(client)
    response = client.get('/admin/topups')
    assert response.status_code == 200
    assert b"Top-Up" in response.data

# --- GET /admin/topups/api --- Success
@patch('routes.admin_routes.send_request')
def test_admin_topups_api_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|' + json.dumps([
        {"id": 1, "user_id": 3, "amount": 50.0, "timestamp": "2024-01-01"}
    ])

    response = client.get('/admin/topups/api')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert data[0]['id'] == 1

# --- GET /admin/topups/api --- Failure
@patch('routes.admin_routes.send_request')
def test_admin_topups_api_failure(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'FAILURE|Could not load'

    response = client.get('/admin/topups/api')
    assert response.status_code == 500
    assert b"Failed to load top-up history" in response.data

# --- GET /admin/topups/api --- Exception
@patch('routes.admin_routes.send_request', side_effect=Exception("DB error"))
def test_admin_topups_api_exception(mock_send, client):
    login_as_admin(client)
    response = client.get('/admin/topups/api')
    assert response.status_code == 500
    assert b"Server error" in response.data

@pytest.fixture
def admin_user_data():
    return {
        "id": 1, "username": "john_doe", "email": "john@example.com",
        "first_name": "John", "last_name": "Doe", "phone_number": "1234567890"
    }

@patch('routes.admin_routes.send_request')
def test_get_users_list(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|[{}]'
    res = client.get('/admin/users?role=customer')
    assert res.status_code == 200
    assert b"customer" in res.data

@patch('routes.admin_routes.send_request')
def test_post_add_user_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|User Added"
    res = client.post('/admin/users/add', data={
        'role': 'customer', 'username': 'test', 'email': 'test@mail.com',
        'password': 'pass', 'first_name': 'F', 'last_name': 'L', 'phone_number': '123'
    })
    assert res.status_code == 200
    assert res.json['success'] is True

@patch('routes.admin_routes.send_request')
def test_post_add_user_forbidden(mock_send, client):
    res = client.post('/admin/users/add')
    assert res.status_code == 403
    
@pytest.mark.skip(reason="Template missing: admin/edit_user.html")
@patch('routes.admin_routes.send_request')
def test_get_edit_user(mock_send, client, admin_user_data):
    login_as_admin(client)
    mock_send.return_value = 'SUCCESS|' + json.dumps(admin_user_data)
    res = client.get('/admin/users/edit/1')
    assert res.status_code == 200
    assert b"john_doe" in res.data

@patch('routes.admin_routes.send_request')
def test_post_edit_user_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS"
    res = client.post('/admin/users/edit/1', data={
        "first_name": "Updated", "last_name": "Name", "phone_number": "9999999"
    })
    assert res.status_code == 200
    assert res.json['success'] is True

@patch('routes.admin_routes.send_request')
def test_post_edit_user_fail(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Error"
    res = client.post('/admin/users/edit/1', data={
        "first_name": "Fail", "last_name": "Test", "phone_number": "000000"
    })
    assert res.status_code == 400

@patch('routes.admin_routes.send_request')
def test_delete_user_redirect(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|Deleted"
    res = client.post('/admin/users/delete/1')
    assert res.status_code == 302  # Redirect expected

@patch('routes.admin_routes.send_request')
def test_user_api_success(mock_send, client, admin_user_data):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|" + json.dumps(admin_user_data)
    res = client.get('/admin/users/api/1')
    assert res.status_code == 200
    assert res.json['username'] == "john_doe"

@patch('routes.admin_routes.send_request')
def test_user_api_not_found(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Not Found"
    res = client.get('/admin/users/api/999')
    assert res.status_code == 404

@patch('routes.admin_routes.send_request')
@pytest.mark.skip(reason="Template missing: admin/view_user_card.html")
def test_view_user_card_success(mock_send, client, admin_user_data):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|" + json.dumps(admin_user_data)
    res = client.get('/admin/users/view/1')
    assert res.status_code == 200
    assert b"john@example.com" in res.data

@patch('routes.admin_routes.send_request')
@pytest.mark.skip(reason="Template missing: admin/view_user_card.html")
def test_view_user_card_not_found(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Not Found"
    res = client.get('/admin/users/view/999')
    assert res.status_code == 200
    assert b"User not found" in res.data

@patch('routes.admin_routes.send_request')
def test_user_report_count_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|3"
    res = client.get('/admin/users/1/report_count')
    assert res.status_code == 200
    assert res.json['count'] == 3

@patch('routes.admin_routes.send_request')
def test_user_booking_count_fallback(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|"
    res = client.get('/admin/users/1/booking_count')
    assert res.status_code == 200
    assert res.json['count'] == 0

# --- GET /admin/scooters (Success) ---
@patch('routes.admin_routes.send_request')
def test_admin_scooters_render_success(mock_send, client):
    login_as_admin(client)
    mock_send.side_effect = [
        'SUCCESS|[]',  # scooters
        'SUCCESS|[]'   # zones
    ]
    res = client.get('/admin/scooters')
    assert res.status_code == 200
    assert "🛴 All Scooters" in res.get_data(as_text=True)


# --- GET /admin/scooters (Failure fallback) ---
@patch('routes.admin_routes.send_request')
def test_admin_scooters_render_error(mock_send, client):
    login_as_admin(client)
    mock_send.side_effect = Exception("DB failure")
    res = client.get('/admin/scooters')
    assert res.status_code == 200
    assert "🛴 All Scooters" in res.get_data(as_text=True)


# --- POST /admin/scooters/add (Success) ---
@patch('routes.admin_routes.send_request')
def test_admin_add_scooter_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|Added"
    form_data = {
        "make": "Yamaha",
        "color": "blue",
        "zone_id": "1",
        "battery": "80",
        "cost": "2.5",
        "status": "available"
    }
    res = client.post('/admin/scooters/add', data=form_data)
    assert res.status_code == 200
    assert res.json['success'] is True

# --- POST /admin/scooters/add (Invalid Zone ID) ---
def test_admin_add_scooter_invalid_zone(client):
    login_as_admin(client)
    form_data = {
        "zone_id": "xyz"  # invalid zone
    }
    res = client.post('/admin/scooters/add', data=form_data)
    assert res.status_code == 400

# --- POST /admin/scooters/edit/<id> (Success) ---
@patch('routes.admin_routes.send_request')
def test_admin_edit_scooter_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|Edited"
    form_data = {
        "make": "Yamaha",
        "color": "red",
        "zone_id": "2",
        "battery": "90",
        "cost": "3.0",
        "status": "maintenance"
    }
    res = client.post('/admin/scooters/edit/5', data=form_data)
    assert res.status_code == 200
    assert res.json['success'] is True

# --- POST /admin/scooters/edit/<id> (Invalid zone) ---
def test_admin_edit_scooter_invalid_zone(client):
    login_as_admin(client)
    res = client.post('/admin/scooters/edit/5', data={"zone_id": "x"})
    assert res.status_code == 400

# --- POST /admin/scooters/delete/<id> ---
def test_admin_delete_scooter(client):
    login_as_admin(client)
    res = client.post('/admin/scooters/delete/5')
    assert res.status_code == 302  # redirect

# --- GET /admin/scooters/api/<id> (Success) ---
@patch('routes.admin_routes.send_request')
def test_admin_scooter_api_success(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "SUCCESS|{" + "\"id\":1," + "\"make\":\"Yamaha\"}"
    res = client.get('/admin/scooters/api/1')
    assert res.status_code == 200
    assert res.json['id'] == 1

# --- GET /admin/scooters/api/<id> (Not found) ---
@patch('routes.admin_routes.send_request')
def test_admin_scooter_api_not_found(mock_send, client):
    login_as_admin(client)
    mock_send.return_value = "FAILURE|Scooter not found"
    res = client.get('/admin/scooters/api/1')
    assert res.status_code == 404

# --- GET /admin/scooters/api/<id> (Exception) ---
@patch('routes.admin_routes.send_request', side_effect=Exception("DB down"))
def test_admin_scooter_api_exception(mock_send, client):
    login_as_admin(client)
    res = client.get('/admin/scooters/api/1')
    assert res.status_code == 500

