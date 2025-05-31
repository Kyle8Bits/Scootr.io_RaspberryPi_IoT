from flask import Blueprint, render_template, request, redirect, session, url_for
from socket_com.send_socket import send_request
import json
from datetime import datetime
from utils.session_utils import update_session_balance
from .qr_scanner import open_scanner


booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/booking')
def booking():
    user_id = session.get('user_id')
    if 'user_id' not in session:
        return redirect(url_for('user.login'))
    if session['role'] == "admin":
        return redirect(url_for('admin.admin_home'))
    if session['role'] == "engineer":
        return redirect(url_for('engineer.engineer_home'))

    response = send_request("GET_ALL_SCOOTER")
    status = response.split('|')[0]

    if not update_session_balance(user_id):
        return redirect(url_for('profile.profile', error="⚠️"))

    if status == "SUCCESS":
        all_scooters = json.loads(response.split("|")[1])
        scooters = [s for s in all_scooters if s.get("status") == "available"]
    else:
        scooters = []

    message = request.args.get('message')
    return render_template('booking.html', scooters=scooters, message=message)


@booking_bp.route('/booking/camera')
def open_camera():
    username = session['user']
    response = open_scanner(username)
    print(f"Response from QR scanner: {response}")
    if response == "NO_USER_FOUND":
        return redirect(url_for('booking.booking', message="❌ Fail to login"))
    elif response == "NOT_BOOKED":
        return redirect(url_for('booking.booking', message="❌ You have not book this scooter"))
    elif response == "SUCCESS_CHECK_IN":
        return redirect(url_for('booking.booking', message="✅ You have unlock this scooter"))
    elif response == "SUCCESS_CHECK_OUT":
        return redirect(url_for('booking.booking', message="✅ You have lock this scooter"))



@booking_bp.route('/confirm_booking', methods=['GET'])
def confirm_booking():
    scooter_id = request.args.get('scooter_id')  # Get scooter_id from the URL query parameter
    if scooter_id:
        # Send a request to fetch scooter details based on the scooter_id
        response = send_request(f"GET_SCOOTER_DETAILS|{scooter_id}")
        status = response.split('|')[0]
        if status == "SUCCESS":
            scooter = json.loads(response.split("|")[1])
            return render_template('confirm_booking.html', scooter=scooter, comments=scooter['comments'])
    # If scooter_id is not found or invalid, redirect to the booking page
    return redirect(url_for('booking.booking', message="❌ Invalid scooter selection."))

@booking_bp.route('/confirm_booking', methods=['POST'])
def add_comment():
    scooter_id = request.args.get('scooter_id')
    comment = request.form.get('comment', '').strip()
    username = session['user']
    if scooter_id and comment:
        # Send a request to add the comment to the scooter
        response = send_request(f"ADD_COMMENT|{username}|{scooter_id}|{comment}")
        print("DEBUG send_request response:", response)

        status = response.split('|')[0]
        if status == "SUCCESS":
            return redirect(url_for('booking.booking', message="✅ Comment added successfully!"))
    return redirect(url_for('booking.booking', message="❌ Failed to add comment."))


@booking_bp.route('/book', methods=['POST'])
def book_scooter():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    scooter_id = request.form['scooter_id']
    checkin_time = request.form['time']  # This is the selected check-in time
    date = request.form['date']  # This is the selected date


    try:
        checkin_datetime = datetime.strptime(f"{date} {checkin_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return redirect(url_for('booking.booking', message="❌ Invalid date or time format."))
   
    current_datetime = datetime.now()

    if checkin_datetime < current_datetime:
        return redirect(url_for('booking.booking', message="❌ Selected date and time must be in the future."))

    response = send_request(f"BOOK_THE_SCOOTER|{session['user_id']}|{scooter_id}|{date}|{checkin_time}")
    result = response.split("|")[0]

    if result == "SUCCESS":
        return redirect(url_for('booking.booking', message="✅ Booking successful!"))
    if result == "INSUFFICIENT_BALANCE":
        return redirect(url_for('booking.booking', message="❌ Insufficient balance. Please recharge your account."))
    else:
        return redirect(url_for('booking.booking', message="❌ Booking failed."))
