import json
from flask import Blueprint, render_template, request, redirect, url_for, session
from socket_com.send_socket import send_request
from flask import flash, redirect, url_for
from flask_mail import Mail

mail = Mail()


def update_session_balance(user_id):
    """
    Update session['balance'] by fetching fresh user data from backend.
    """
    response = send_request(f"GET_BY_ID|{user_id}")
    if response.startswith("SUCCESS"):
        user_data = json.loads(response.split("|", 1)[1])
        session["balance"] = float(user_data["balance"])
        return True
    return False


def get_invoice_params(booking_id):
    """
    Retrieves invoice-related parameters via socket and prepares them
    for use in routes like invoice generation or sharing.

    Args:
        booking_id (str): ID of the booking to retrieve data for.

    Returns:
        Tuple: (scooter: dict, checkout_time: str, booking: dict, total_price: float)
               or None if retrieval fails.
    """
    response = send_request(f"GET_INVOICE|{booking_id}")
    print("🧾 Raw invoice response:", response)

    if not response.startswith("SUCCESS|"):
        flash("❌ Failed to retrieve invoice data.")
        return None

    _, raw_data = response.split("|", 1)
    data = json.loads(raw_data)

    scooter = {
        "cost_per_minute": data["cost_per_minute"],
        "make": data["make"],
        "id": data["scooter_id"]
    }

    booking = {
        "checkin_time": data["checkin_time"]
    }

    return scooter, data["checkout_time"], booking, data["total_price"]