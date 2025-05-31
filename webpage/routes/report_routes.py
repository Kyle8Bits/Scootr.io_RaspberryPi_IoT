from flask import Blueprint, current_app, request, redirect, url_for, flash, render_template, session
from socket_com.send_socket import send_request

report_bp = Blueprint('report', __name__)

@report_bp.route('/report_issue', methods=['GET'])
def report_issue():
    scooter_id = request.args.get('scooter_id')
    return render_template('report_issue.html', scooter_id=scooter_id, google_maps_api_key=current_app.config["GOOGLE_MAPS_API_KEY"])

@report_bp.route('/submit_issue', methods=['POST'])
def submit_issue():
    user_id = session.get('user_id')  # 🧠 get customer id from session
    if not user_id:
        flash("❌ Session expired. Please log in again.", "error")
        return redirect(url_for('user.login'))

    scooter_id = request.form.get('scooter_id')
    issue_type = request.form.get('issue_type')
    additional_details = request.form.get('additional_details', '')
    
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if not scooter_id or not issue_type:
        flash("❌ Missing required fields.", "error")
        return redirect(url_for('report.report_issue', scooter_id=scooter_id))

    response = send_request(f"REPORT_ISSUE|{user_id}|{scooter_id}|{issue_type}|{additional_details}|{latitude}|{longitude}")

    if response.startswith("SUCCESS"):
        return redirect(url_for('booking.booking', message = "Thank you. Your report has been submited"))  # ✅ Go back to booking after success
    else:
        flash("❌ Failed to report issue. Please try again.", "error")
        return redirect(url_for('report.report_issue', scooter_id=scooter_id))

@report_bp.route('/get_scooter_details', methods=['GET'])
def get_scooter_details():
    scooter_id = request.args.get('scooter_id')
    if not scooter_id:
        return {"error": "Scooter ID is required."}, 400

    response = send_request(f"GET_SCOOTER_DETAILS|{scooter_id}")
    status = response.split('|')[0]

    if status == "SUCCESS":
        scooter_details = response.split("|")[1]
        return scooter_details, 200
    else:
        return {"error": "Failed to fetch scooter details."}, 500