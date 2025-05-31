from unittest.mock import patch, MagicMock
import sys
import re
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
from master_pi.service.EngineerService import Engineer  # Adjust if class name is different
from master_pi.service.ScooterService import Scooter  # Adjust if class name is different

import json

def test_get_issues_assigned_success():
    mock_engineer_id = 42
    mock_issues = [{
        "id": 1,
        "scooter_id": 10,
        "customer_id": 5,
        "issue_type": "Flat tire",
        "additional_details": "Rear wheel flat",
        "reported_at": "2024-01-01 10:00",
        "status": "Assigned",
        "updated_at": "2024-01-01 11:00",
        "latitude": 1.23,
        "longitude": 4.56,
        "approved_at": "2024-01-01 10:30",
        "resolved_at": None
    }]

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = mock_issues

        result = Engineer.get_issues_assigned_to_engineer(mock_engineer_id)

        assert result.startswith("SUCCESS|")
        data = json.loads(result.split("|", 1)[1])
        assert isinstance(data, list)
        assert data[0]["issue_type"] == "Flat tire"

        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_mark_resolved_success():
    issue_id = 1
    engineer_id = 42
    resolution_type = "Fixed"
    resolution_details = "Replaced wheel"

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # simulate scooter_id fetch
        mock_cursor.fetchone.return_value = [7]

        result = Engineer.mark_resolved(issue_id, engineer_id, resolution_type, resolution_details)

        assert result == "SUCCESS"

        # Verify multiple SQL executions
        assert mock_cursor.execute.call_count >= 3
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_mark_resolved_failure():
    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Simulated DB failure")

        result = Engineer.mark_resolved(1, 42, "Fixed", "Replaced wheel")
        assert result.startswith("FAILURE|")


def test_get_resolved_issues_success():
    mock_engineer_id = 99
    mock_data = [{
        "issue_id": 1,
        "scooter_id": 101,
        "issue_type": "Brake failure",
        "approved_at": "2024-03-01 12:00",
        "resolved_at": "2024-03-02 15:00",
        "resolution_type": "Repaired",
        "resolution_details": "Brake pad replaced"
    }]

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = mock_data

        result = Engineer.get_resolved_issues(mock_engineer_id)

        assert result.startswith("SUCCESS|")
        data = json.loads(result.split("|", 1)[1])
        assert isinstance(data, list)
        assert data[0]["issue_id"] == 1

        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_resolved_issues_failure():
    mock_engineer_id = 99

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("DB error")

        result = Engineer.get_resolved_issues(mock_engineer_id)

        assert result.startswith("FAILURE|")
        assert "DB error" in result

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_all_approve_issues_details_success():
    issue_ids_result = [{"issue_id": 1}, {"issue_id": 2}]
    issues_result = [
        {
            "id": 1,
            "scooter_id": 5,
            "customer_id": 11,
            "issue_type": "Flat tire",
            "additional_details": "Back tire flat",
            "latitude": 1.234,
            "longitude": 2.345,
            "reported_at": "2024-04-01T12:00:00",
            "status": "approved",
            "updated_at": "2024-04-01T12:10:00"
        }
    ]

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Sequential fetchall return values
        mock_cursor.fetchall.side_effect = [issue_ids_result, issues_result]

        result = Engineer.get_all_approve_issues_details()

        assert result.startswith("SUCCESS|")
        data = json.loads(result.split("|", 1)[1])
        assert isinstance(data, list)
        assert data[0]["issue_type"] == "Flat tire"

        assert mock_cursor.execute.call_count == 2
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_all_approve_issues_details_empty():
    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        result = Engineer.get_all_approve_issues_details()
        assert result == "SUCCESS|[]"

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_all_approve_issues_details_failure():
    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Simulated DB error")

        result = Engineer.get_all_approve_issues_details()
        assert result.startswith("FAILURE|Simulated DB error")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_issues_assigned_to_engineer_success():
    mock_engineer_id = 42
    mock_data = [
        {
            "id": 1,
            "scooter_id": 101,
            "customer_id": 22,
            "issue_type": "Battery low",
            "additional_details": "Drains quickly",
            "reported_at": "2024-01-01 12:00",
            "status": "assigned",
            "updated_at": "2024-01-01 13:00",
            "latitude": 12.34,
            "longitude": 56.78,
            "approved_at": "2024-01-01 12:30",
            "resolved_at": None
        }
    ]

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = mock_data

        result = Engineer.get_issues_assigned_to_engineer(mock_engineer_id)

        assert result.startswith("SUCCESS|")
        data = json.loads(result.split("|", 1)[1])
        assert isinstance(data, list)
        assert data[0]["issue_type"] == "Battery low"

        mock_cursor.execute.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_get_issues_assigned_to_engineer_failure():
    mock_engineer_id = 42

    with patch('master_pi.service.EngineerService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Simulated error")

        result = Engineer.get_issues_assigned_to_engineer(mock_engineer_id)

        assert result.startswith("FAILURE|Simulated error")

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_dashboard_api_success(client):
    mock_engineer_id = 42
    mock_issues = [{"scooter_id": 1, "status": "assigned"}]
    mock_resolved = [{
        "approved_at": "2024-05-01 10:00:00",
        "resolved_at": "2024-05-01 11:00:00"
    }]
    mock_scooter = {"power_remaining": 87}

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.side_effect = [
            f"SUCCESS|{json.dumps(mock_issues)}",           # GET_ENGINEER_ISSUES
            f"SUCCESS|{json.dumps(mock_resolved)}",         # GET_ENGINEER_RESOLVED_ISSUES
            f"SUCCESS|{json.dumps(mock_scooter)}"           # GET_SCOOTER_BY_ID
        ]

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = mock_engineer_id

        res = client.get('/engineer/home/api')
        assert res.status_code == 200
        data = res.get_json()
        assert "average_battery" in data
        assert "resolved_issues" in data
        assert isinstance(data["recent_resolutions"], list)

def test_dashboard_api_unauthorized(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'  # not engineer

    res = client.get('/engineer/home/api')
    assert res.status_code == 403
    assert res.get_json()['error'] == "Unauthorized"

def test_engineer_get_scooter_success(client):
    mock_scooter_id = 1
    mock_scooter_data = {
        "id": mock_scooter_id,
        "make": "Yamaha",
        "battery": 75,
        "status": "available"
    }

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(mock_scooter_data)}"

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 99

        res = client.get(f"/engineer/scooter/{mock_scooter_id}")
        assert res.status_code == 200
        data = res.get_json()
        assert data["id"] == mock_scooter_id
        assert data["status"] == "available"

def test_engineer_get_scooter_not_found(client):
    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = "FAILURE|Scooter not found"

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 99

        res = client.get("/engineer/scooter/999")
        assert res.status_code == 404
        assert "error" in res.get_json()

def test_engineer_get_scooter_unauthorized(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'  # not engineer

    res = client.get("/engineer/scooter/1")
    assert res.status_code == 403
    assert res.get_json()['error'] == "Forbidden"

def test_engineer_resolved_issues_api_success(client):
    mock_issues = [
        {"issue_id": 1, "resolution_type": "Fix", "resolution_details": "Replaced tire"}
    ]

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(mock_issues)}"

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 99

        res = client.get("/engineer/report/api")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert data[0]["issue_id"] == 1

def test_engineer_resolved_issues_api_forbidden(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'

    res = client.get("/engineer/report/api")
    assert res.status_code == 403
    assert res.get_json()['error'] == "Forbidden"

def test_engineer_resolved_issues_api_failure(client):
    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.side_effect = Exception("Test failure")

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 99

        res = client.get("/engineer/report/api")
        assert res.status_code == 500
        assert res.get_json()['error'] == "Server error"

def test_engineer_issues_api_success(client):
    mock_issues = [
        {"id": 1, "status": "assigned"},
        {"id": 2, "status": "assigned"}
    ]

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(mock_issues)}"

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 99

        res = client.get("/engineer/issues/api")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1

def test_engineer_issues_api_forbidden(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'

    res = client.get("/engineer/issues/api")
    assert res.status_code == 403
    assert res.get_json()['error'] == "Forbidden"

def test_engineer_resolve_issue_success(client):
    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = "SUCCESS|Issue resolved"

        with client.session_transaction() as sess:
            sess['role'] = 'engineer'
            sess['user_id'] = 88

        res = client.post("/engineer/issues/1/resolve", json={
            "resolution_type": "Fix",
            "resolution_details": "Patched tire"
        })

        assert res.status_code == 200
        assert res.get_json()['success'] is True

def test_engineer_resolve_issue_missing_details(client):
    with client.session_transaction() as sess:
        sess['role'] = 'engineer'
        sess['user_id'] = 88

    res = client.post("/engineer/issues/1/resolve", json={
        "resolution_type": "Fix",
        "resolution_details": ""
    })
    assert res.status_code == 400
    assert res.get_json()['error'] == "Resolution details required"

def test_engineer_resolve_issue_unauthorized(client):
    with client.session_transaction() as sess:
        sess['role'] = 'customer'

    res = client.post("/engineer/issues/1/resolve", json={
        "resolution_type": "Fix",
        "resolution_details": "Done"
    })
    assert res.status_code == 403
    assert res.get_json()['error'] == "Unauthorized"
    
def test_engineer_map_issues_success(client):
    mock_issues = [
        {"id": 1, "latitude": 10.0, "longitude": 20.0, "status": "approved"}
    ]

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = f"SUCCESS|{json.dumps(mock_issues)}"

        res = client.get("/engineer/map/issues")
        assert res.status_code == 200
        data = res.get_json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1

def test_engineer_map_issues_failure(client):
    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.side_effect = Exception("Map fail")

        res = client.get("/engineer/map/issues")
        assert res.status_code == 500
        assert res.get_json()['error'] == "Exception occurred"

def test_engineer_issue_detail_success(client):
    mock_issue = {"id": 1, "issue_type": "Flat tire"}
    mock_scooter = {"id": 1, "status": "available"}

    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.side_effect = [
            f"SUCCESS|{json.dumps(mock_issue)}",
            f"SUCCESS|{json.dumps(mock_scooter)}"
        ]

        res = client.get("/engineer/issue?issue_id=1&scooter_id=1")
        assert res.status_code == 200
        assert b"Flat tire" in res.data or b"available" in res.data

def test_engineer_issue_detail_missing_params(client):
    res = client.get("/engineer/issue?issue_id=1")
    assert res.status_code == 400
    assert b"Missing issue_id or scooter_id" in res.data

def test_engineer_issue_detail_load_failure(client):
    with patch('routes.engineer_routes.send_request') as mock_send:
        mock_send.return_value = "FAILURE|Issue not found"

        res = client.get("/engineer/issue?issue_id=1&scooter_id=1")
        assert res.status_code == 500
        assert b"Error loading issue details" in res.data
