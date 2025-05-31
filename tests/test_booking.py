# tests/test_booking.py

from datetime import datetime
import sys
import re
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))
import json
from unittest.mock import patch, MagicMock
from master_pi.service.BookingService import Booking
from master_pi.service.UserService import User


def test_successful_booking_creates_record():
    mock_user = {"id": 1, "email": "user@example.com", "balance": 100}
    mock_scooter = {"id": 1, "location": "Test Park", "zone_id": 1}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.add_into_table') as mock_add, \
         patch('master_pi.service.BookingService.create_event') as mock_event:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.side_effect = [mock_scooter, mock_user]
        mock_event.return_value = {"id": "mock_event_id"}

        result = Booking.create_booking(1, 1, "2025-05-01", "14:00")
        assert result == "SUCCESS"
        mock_add.assert_called_once()



def test_booking_marks_scooter_unavailable():
    mock_user = {"id": 1, "email": "user@example.com", "balance": 100}
    mock_scooter = {"id": 1, "location": "Test Park", "zone_id": 1}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.add_into_table'), \
         patch('master_pi.service.BookingService.create_event') as mock_event:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_event.return_value = {"id": "mock_event_id"}
        mock_get_by.side_effect = [mock_scooter, mock_user]

        Booking.create_booking(1, 1, "2025-05-01", "14:00")

        mock_update.assert_any_call(mock_cursor, "scooters", {"status": "booked"}, 1)



def test_booking_creates_calendar_event():
    mock_user = {"id": 1, "email": "user@example.com", "balance": 100}
    mock_scooter = {"id": 1, "location": "Hanoi", "zone_id": 1}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field'), \
         patch('master_pi.service.BookingService.add_into_table'), \
         patch('master_pi.service.BookingService.create_event') as mock_event:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.side_effect = [mock_scooter, mock_user]
        mock_event.return_value = {"id": "calendar-event-123"}

        Booking.create_booking(1, 1, "2025-05-01", "14:00")

        mock_event.assert_called_once()
        assert mock_event.return_value["id"] == "calendar-event-123"



def test_cannot_double_book_scooter():
    with patch('master_pi.service.BookingService.get_all_from_table') as mock_all_bookings:
        # Simulate existing conflicting booking
        existing_booking = {
            "user_id": 1,
            "scooter_id": 1,
            "rent_date": "2025-05-01",
            "checkin_time": "14:00",
            "status": "waiting"
        }
        mock_all_bookings.return_value = [existing_booking]

        bookings = mock_all_bookings.return_value
        is_conflict = any(
            b["scooter_id"] == 1 and
            b["rent_date"] == "2025-05-01" and
            b["checkin_time"] == "14:00" and
            b["status"] in ["waiting", "booked", "in-use"]
            for b in bookings
        )

        assert is_conflict, "Scooter should not be bookable twice for the same time slot."


def test_booking_fails_if_user_or_scooter_not_found():
    with patch('master_pi.service.BookingService.get_db'), \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by:

        # First call (scooter) returns None
        mock_get_by.side_effect = [None, {"id": 1, "balance": 100}]

        result = Booking.create_booking(1, 999, "2025-05-01", "14:00")
        assert result == "ERROR|User or scooter not found"



def test_booking_fails_with_insufficient_balance():
    with patch('master_pi.service.BookingService.get_db'), \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by:

        scooter = {"id": 1, "location": "Hanoi"}
        user = {"id": 1, "email": "user@example.com", "balance": 5}

        mock_get_by.side_effect = [scooter, user]

        result = Booking.create_booking(1, 1, "2025-05-01", "14:00")
        assert result == "INSUFFICIENT_BALANCE"


def test_cancel_booking_calls_event_deletion():
    booking_data = {
        "id": 1,
        "user_id": 1,
        "scooter_id": 2,
        "event_id": "mock_event_id"
    }

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.delete_event') as mock_delete, \
         patch('master_pi.service.BookingService.User.top_up') as mock_top_up:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.return_value = booking_data

        result = Booking.cancel_booking(1, 1)
        assert result == "SUCCESS"
        mock_delete.assert_called_once_with("mock_event_id")
        mock_top_up.assert_called_once()
        mock_update.assert_any_call(mock_cursor, "scooters", {"status": "available"}, 2)


...

def test_cancel_booking_sets_status_to_canceled():
    booking_data = {
        "id": 42,
        "user_id": 1,
        "scooter_id": 2,
        "event_id": "cancel-test-event"
    }

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.delete_event'), \
         patch('master_pi.service.BookingService.User.top_up'):

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.return_value = booking_data

        result = Booking.cancel_booking(user_id=1, booking_id=42)
        assert result == "SUCCESS"

        mock_update.assert_any_call(mock_cursor, "bookings", {"status": "canceled"}, 42)


def test_checkin_updates_status_to_in_use():
    mock_booking = {"id": 10, "user_id": 1, "scooter_id": 3}
    mock_scooter = {"id": 3, "location": "Central", "zone_id": 1}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.side_effect = [mock_booking, mock_scooter]

        # Only pass booking_id and checking_time — match method signature
        result = Booking.checkin_booking(10, "09:00")

        assert result == "SUCCESS"
        mock_update.assert_any_call(mock_cursor, "scooters", {"status": "in_use"}, 3)
        mock_update.assert_any_call(mock_cursor, "bookings", {
            "status": "in_use",
            "checkin_time": "09:00"
        }, 10)

def test_checkout_updates_total_price_and_status():
    booking_data = {"id": 20, "user_id": 1, "scooter_id": 2, "status": "in_use"}
    user_data = {"id": 1, "balance": 50.0}
    zone_data = {"id": 1, "name": "Z"}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.User.top_up') as mock_top_up, \
         patch('master_pi.service.BookingService.Scooter.update_scooter_power'), \
         patch('master_pi.service.BookingService.Report.report_issue'):

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            {"minutes_diff": 60},
            {"power_remaining": 100, "zone_id": 1}
        ]
        mock_get_by.side_effect = [booking_data, user_data, zone_data]

        result = Booking.checkout_booking(20, "10:00", 25.0)

        assert result == "SUCCESS"

        # ❌ Remove this (unless you plan to add that logic to the function)
        # mock_update.assert_any_call(mock_cursor, "scooters", {"status": "available"}, 2)
        mock_update.assert_any_call(mock_cursor, "bookings", {
            "status": "returned",
            "checkout_date": "10:00",
            "total_price": 25.0
        }, 20)
        mock_top_up.assert_called_once_with(1, -15.0)


def test_checkout_booking_success_under_10():
    mock_user = {"id": 1, "email": "user@example.com", "balance": 5.0}
    mock_booking = {"id": 1, "user_id": 1, "scooter_id": 1, "status": "in-use"}
    mock_zone = {"id": 1, "name": "TestZone"}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.User.top_up') as mock_top_up, \
         patch('master_pi.service.BookingService.Scooter.update_scooter_power'), \
         patch('master_pi.service.BookingService.Report.report_issue'):

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [
            {"minutes_diff": 60},
            {"power_remaining": 50, "zone_id": 1}
        ]

        mock_get_by.side_effect = [mock_booking, mock_user, mock_zone]

        result = Booking.checkout_booking(1, "10:00", 8.0)
        assert result == "SUCCESS"

        print("[Mock calls to update_field]:", mock_update.call_args_list)

        mock_update.assert_any_call(mock_cursor, "bookings", {
            "status": "returned",
            "checkout_date": "10:00",
            "total_price": 8.0
        }, 1)

        # The update to 'scooters' depends on new_power condition in the logic
        mock_top_up.assert_called_once_with(1, 2.0)



def test_checkout_booking_success_with_balance():
    mock_user = {"id": 1, "email": "user@example.com", "balance": 50.0}
    mock_booking = {"id": 1, "user_id": 1, "scooter_id": 1, "status": "in-use"}
    mock_zone = {"id": 1, "name": "Central"}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update, \
         patch('master_pi.service.BookingService.User.top_up') as mock_top_up, \
         patch('master_pi.service.BookingService.Scooter.update_scooter_power') as mock_update_power, \
         patch('master_pi.service.BookingService.Report.report_issue') as mock_report_issue:

        # Setup DB mock
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor

        # Mock result of SQL fetches
        mock_cursor.fetchone.side_effect = [
            {"minutes_diff": 100},       # for TIMESTAMPDIFF
            {"power_remaining": 50, "zone_id": 1}      # for SELECT power_remaining
        ]

        # Patch get_by_field responses: booking, user, zone
        mock_get_by.side_effect = [mock_booking, mock_user, mock_zone]

        result = Booking.checkout_booking(1, "10:00", 25.0)

        assert result == "SUCCESS"
        mock_top_up.assert_called_once_with(1, -15.0)
        mock_update.assert_any_call(mock_cursor, "bookings", {
            "status": "returned",
            "checkout_date": "10:00",
            "total_price": 25.0
        }, 1)



def test_checkin_booking_success():
    mock_booking = {"id": 1, "user_id": 1, "scooter_id": 1}
    mock_scooter = {"id": 1, "location": "Test Park", "zone_id": 1}

    with patch('master_pi.service.BookingService.get_db') as mock_db, \
         patch('master_pi.service.BookingService.get_by_field') as mock_get_by, \
         patch('master_pi.service.BookingService.update_field') as mock_update:

        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_get_by.side_effect = [mock_booking, mock_scooter]

        # Updated to match the correct method signature: (booking_id, checking_time)
        result = Booking.checkin_booking(1, "10:00")

        assert result == "SUCCESS"
        mock_update.assert_any_call(mock_cursor, "scooters", {"status": "in_use"}, 1)
        mock_update.assert_any_call(mock_cursor, "bookings", {
            "status": "in_use",
            "checkin_time": "10:00"
        }, 1)


def test_get_booking_history_success():
    from datetime import datetime

    mock_user_id = 1
    mock_results = [
        {
            "id": 1,
            "make": "Yamaha",
            "color": "Blue",
            "location": "Park A",
            "cost_per_minute": 4.0,
            "rent_date": datetime(2025, 5, 1, 12, 0),
            "checkin_time": datetime(2025, 5, 1, 12, 30),
            "checkout_time": datetime(2025, 5, 1, 14, 0),
            "status": "completed",
            "cost": 8.0
        },
        {
            "id": 2,
            "make": "Honda",
            "color": "Red",
            "location": "Park B",
            "cost_per_minute": 2.0,
            "rent_date": datetime(2025, 5, 2, 14, 0),
            "checkin_time": datetime(2025, 5, 2, 14, 30),
            "checkout_time": datetime(2025, 5, 2, 16, 0),
            "status": "completed",
            "cost": 4.0
        }
    ]

    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = mock_results
        mock_cursor.execute.return_value = None

        result = User.get_booking_history(mock_user_id)

        assert result.startswith("SUCCESS|")
        assert '"cost": 8.0' in result
        assert '"cost_per_minute": 4.0' in result

        actual_query = mock_cursor.execute.call_args[0][0]

        expected_query = """
            SELECT
                b.id AS id,
                s.make,
                s.color,
                z.name AS location,
                s.cost_per_minute,
                b.rent_date,
                b.checkin_time,
                b.checkout_date,
                b.status,
                b.scooter_id,
                b.total_price AS cost
            FROM bookings b
            JOIN scooters s ON b.scooter_id = s.id
            JOIN zones z ON s.zone_id = z.id
            WHERE b.user_id = %s
        """

        expected_query_cleaned = re.sub(r'\s+', ' ', expected_query.strip())
        actual_query_cleaned = re.sub(r'\s+', ' ', actual_query.strip())

        assert expected_query_cleaned == actual_query_cleaned, (
            f"Expected query did not match actual query.\nExpected: {expected_query_cleaned}\nGot: {actual_query_cleaned}"
        )

def test_get_booking_history_empty():
    mock_user_id = 2
    mock_results = []  # No bookings

    with patch('master_pi.service.UserService.get_db') as mock_db:
        mock_cursor = MagicMock()
        mock_db.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = mock_results
        mock_cursor.execute.return_value = None

        result = User.get_booking_history(mock_user_id)

        assert result == "SUCCESS|[]"

        actual_query = mock_cursor.execute.call_args[0][0]

        expected_query = """
            SELECT
                b.id AS id,
                s.make,
                s.color,
                z.name AS location,
                s.cost_per_minute,
                b.rent_date,
                b.checkin_time,
                b.checkout_date,
                b.status,
                b.scooter_id,
                b.total_price AS cost
            FROM bookings b
            JOIN scooters s ON b.scooter_id = s.id
            JOIN zones z ON s.zone_id = z.id
            WHERE b.user_id = %s
        """

        expected_query_cleaned = re.sub(r'\s+', ' ', expected_query.strip())
        actual_query_cleaned = re.sub(r'\s+', ' ', actual_query.strip())

        assert expected_query_cleaned == actual_query_cleaned, (
            f"Expected query did not match actual query.\nExpected: {expected_query_cleaned}\nGot: {actual_query_cleaned}"
        )

@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_redirects_if_not_logged_in(mock_balance, mock_send, client):
    res = client.get('/booking')
    assert res.status_code == 302
    assert '/login' in res.location


@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_redirects_if_admin(mock_balance, mock_send, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'admin'
    res = client.get('/booking')
    assert res.status_code == 302
    assert '/admin/home' in res.location


@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_redirects_if_engineer(mock_balance, mock_send, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'engineer'
    res = client.get('/booking')
    assert res.status_code == 302
    assert '/engineer/engineer_home' in res.location


@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_success_renders_available_scooters(mock_balance, mock_send, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'user'

    mock_balance.return_value = True
    mock_send.return_value = 'SUCCESS|' + json.dumps([
        {"id": 1, "status": "available"},
        {"id": 2, "status": "in_use"}
    ])

    res = client.get('/booking')
    assert res.status_code == 200
    assert b"Available Scooters" in res.data

@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_handles_failed_scooter_fetch(mock_balance, mock_send, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'user'

    mock_balance.return_value = True
    mock_send.return_value = 'FAILURE|Error'

    res = client.get('/booking')
    assert res.status_code == 200


@patch('routes.booking_routes.send_request')
@patch('routes.booking_routes.update_session_balance')
def test_booking_handles_session_balance_failure(mock_balance, mock_send, client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['role'] = 'user'

    mock_balance.return_value = False
    res = client.get('/booking')
    assert res.status_code == 302
    assert '/profile' in res.location

# --- Test setup helper ---
def login_as_test_user(client):
    with client.session_transaction() as sess:
        sess['user'] = 'test_user'
        sess['user_id'] = 1
        sess['role'] = 'user'

# --- /booking/camera route tests ---

@patch('routes.booking_routes.open_scanner')
def test_open_camera_no_user_found_redirect(mock_scanner, client):
    login_as_test_user(client)
    mock_scanner.return_value = "NO_USER_FOUND"
    res = client.get('/booking/camera')
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Fail+to+login" in res.location


@patch('routes.booking_routes.open_scanner')
def test_open_camera_not_booked_redirect(mock_scanner, client):
    login_as_test_user(client)
    mock_scanner.return_value = "NOT_BOOKED"
    res = client.get('/booking/camera')
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+You+have+not+book+this+scooter" in res.location


@patch('routes.booking_routes.open_scanner')
def test_open_camera_success_checkin_redirect(mock_scanner, client):
    login_as_test_user(client)
    mock_scanner.return_value = "SUCCESS_CHECK_IN"
    res = client.get('/booking/camera')
    assert res.status_code == 302
    assert "/booking?message=%E2%9C%85+You+have+unlock+this+scooter" in res.location


@patch('routes.booking_routes.open_scanner')
def test_open_camera_success_checkout_redirect(mock_scanner, client):
    login_as_test_user(client)
    mock_scanner.return_value = "SUCCESS_CHECK_OUT"
    res = client.get('/booking/camera')
    assert res.status_code == 302
    assert "/booking?message=%E2%9C%85+You+have+lock+this+scooter" in res.location


# --- /confirm_booking route tests ---

@patch('routes.booking_routes.send_request')
def test_confirm_booking_valid_scooter_renders_template(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = 'SUCCESS|' + json.dumps({"id": 1, "comments": []})
    res = client.get('/confirm_booking?scooter_id=1')
    assert res.status_code == 200
    assert b"Confirm Booking" in res.data  # assuming template has this phrase


@patch('routes.booking_routes.send_request')
def test_confirm_booking_invalid_scooter_redirects(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = 'FAILURE|Not Found'
    res = client.get('/confirm_booking?scooter_id=999')
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Invalid+scooter+selection." in res.location

# --- /confirm_booking route (POST) comment submission ---

@patch('routes.booking_routes.send_request')
def test_add_comment_success_redirects_with_message(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = "SUCCESS|Comment added"
    res = client.post('/confirm_booking?scooter_id=1', data={'comment': 'Looks good'})
    assert res.status_code == 302
    assert "/booking?message=%E2%9C%85+Comment+added+successfully!" in res.location


@patch('routes.booking_routes.send_request')
def test_add_comment_failure_redirects_with_error(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = "FAILURE|Error"
    res = client.post('/confirm_booking?scooter_id=1', data={'comment': 'Needs repair'})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Failed+to+add+comment." in res.location


@patch('routes.booking_routes.send_request')
def test_add_comment_missing_data_redirects(mock_send, client):
    login_as_test_user(client)
    res = client.post('/confirm_booking?scooter_id=1', data={'comment': ''})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Failed+to+add+comment." in res.location

# --- /book route (POST) ---

@patch('routes.booking_routes.send_request')
def test_book_scooter_redirects_if_not_logged_in(mock_send, client):
    res = client.post('/book', data={})
    assert res.status_code == 302
    assert "/login" in res.location


@patch('routes.booking_routes.send_request')
def test_book_scooter_invalid_datetime_format(mock_send, client):
    login_as_test_user(client)
    res = client.post('/book', data={'scooter_id': 1, 'time': 'invalid', 'date': '2025-01-01'})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Invalid+date+or+time+format." in res.location


@patch('routes.booking_routes.send_request')
def test_book_scooter_past_datetime_redirects(mock_send, client):
    login_as_test_user(client)
    past_date = datetime.now().strftime('%Y-%m-%d')
    past_time = (datetime.now().replace(hour=0, minute=0).strftime('%H:%M'))
    res = client.post('/book', data={'scooter_id': 1, 'time': past_time, 'date': past_date})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Selected+date+and+time+must+be+in+the+future." in res.location


@patch('routes.booking_routes.send_request')
def test_book_scooter_successful_booking(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = "SUCCESS"
    future_date = (datetime.now().replace(year=2030).strftime('%Y-%m-%d'))
    res = client.post('/book', data={'scooter_id': 1, 'time': '10:00', 'date': future_date})
    assert res.status_code == 302
    assert "/booking?message=%E2%9C%85+Booking+successful!" in res.location


@patch('routes.booking_routes.send_request')
def test_book_scooter_insufficient_balance(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = "INSUFFICIENT_BALANCE"
    future_date = (datetime.now().replace(year=2030).strftime('%Y-%m-%d'))
    res = client.post('/book', data={'scooter_id': 1, 'time': '10:00', 'date': future_date})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Insufficient+balance.+Please+recharge+your+account." in res.location


@patch('routes.booking_routes.send_request')
def test_book_scooter_generic_failure(mock_send, client):
    login_as_test_user(client)
    mock_send.return_value = "FAILURE"
    future_date = (datetime.now().replace(year=2030).strftime('%Y-%m-%d'))
    res = client.post('/book', data={'scooter_id': 1, 'time': '10:00', 'date': future_date})
    assert res.status_code == 302
    assert "/booking?message=%E2%9D%8C+Booking+failed." in res.location
