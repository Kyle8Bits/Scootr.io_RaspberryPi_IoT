from flask import Blueprint, render_template, request, redirect, session, url_for
from socket_com.send_socket import send_request
import json
from flask_mail import Mail, Message
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from flask import session, request, flash, redirect, url_for
from .pdf import generate_invoice
from utils.session_utils import update_session_balance

import hashlib

profile_bp = Blueprint('profile', __name__)

# --------------------------
# PROFILE PAGE
# --------------------------
@profile_bp.route('/profile')
def profile():
    # ✅ Check if logged in
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login'))

    if not update_session_balance(user_id):
        return redirect(url_for('profile.profile', error="⚠️"))

    # 🔌 Fetch user data from backend
    response = send_request(f"GET_USER_PROFILE|{user_id}")
    print("🔌 RAW socket response:", response)

    if not response:
        print("❌ Empty response from backend.")
        return redirect(url_for('user.login'))

    parts = response.split('|', 1)
    if len(parts) != 2 or parts[0] != "SUCCESS":
        print("❌ Invalid or failed backend response.")
        return redirect(url_for('user.login'))

    try:
        print("🧪 Attempting to parse JSON...")
        user_data = json.loads(parts[1])
        print("✅ Parsed user data:", user_data)
    except Exception as e:
        print("❌ JSON decode error:", e)
        return redirect(url_for('user.login'))

    # ✅ Success — render profile
    return render_template('profile.html', user=user_data)

# --------------------------
# TOP-UP HANDLER
# --------------------------
@profile_bp.route('/top-up', methods=['POST'])
def top_up():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    amount = float(request.form.get('amount', 0))

    response = send_request(f"TOP_UP|{user_id}|{amount}")
    print("💸 Top-up response:", response)

    if response and response.split('|')[0] == "SUCCESS":
        return redirect(url_for('profile.profile'))
    else:
        return redirect(url_for('profile.profile', error="❌ Failed to top up"))


# --------------------------
# UPDATE USER INFO
# --------------------------
@profile_bp.route('/profile/update', methods=['POST'])
def update_info():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    data = {
        'username': request.form.get('username'),
        'email': request.form.get('email'),
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'phone_number': request.form.get('phone_number')
    }

    payload = f"UPDATE_USER_INFO|{user_id}|{json.dumps(data)}"
    response = send_request(payload)
    print("📝 Update info response:", response)

    if response and response.split('|')[0] == "SUCCESS":
        return redirect(url_for('profile.profile'))
    else:
        return redirect(url_for('profile.profile', error="❌ Failed to update info"))

# --------------------------
# CHANGE PASSWORD
# --------------------------
@profile_bp.route('/profile/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    response = send_request(f"GET_USER_BY_ID|{user_id}")
    if not response or not response.startswith("SUCCESS|"):
        flash("❌ Failed to load user info", "error")
        return redirect(url_for('profile.profile'))

    user = json.loads(response.split("|", 1)[1])
    user_email = user.get('email')

    login_response = send_request(f"LOGIN|{user['username']}|{current_password}")
    if not login_response.startswith("SUCCESS|"):
        flash("❌ Current password incorrect", "error")
        return redirect(url_for('profile.profile'))

    if new_password != confirm_password :
        flash("❌ New passwords do not match", "error")
        return redirect(url_for('profile.profile'))
    
    if new_password == current_password :
        flash("❌ New password matchs current password", "error")
        return redirect(url_for('profile.profile'))

    mail = Mail(current_app)
    serializer = URLSafeTimedSerializer(current_app.secret_key)

    token = serializer.dumps({
        "user_id": user_id,
        "new_password": hashlib.sha256(new_password.encode()).hexdigest()
    }, salt="password-change")
    confirm_url = url_for('profile.confirm_password_change', token=token, _external=True)
    msg = Message("Confirm Your Password Change", recipients=[user_email])
    msg.body = f"Click the link to confirm your password change:\n\n{confirm_url}"

    try:
        mail.send(msg)
        flash("📩 Confirmation sent to your Gmail", "success")
    except Exception as e:
        print("❌ Email send failed:", e)
        flash("❌ Email failed to send", "error")

    return redirect(url_for('profile.profile'))

@profile_bp.route('/profile/confirm-password/<token>')
def confirm_password_change(token):
    serializer = URLSafeTimedSerializer(current_app.secret_key)

    try:
        data = serializer.loads(token, salt='password-change', max_age=3600)
        user_id = data['user_id']
        new_hash = data['new_password']

        payload = f"CHANGE_PASSWORD|{user_id}|{new_hash}"
        change_response = send_request(payload)
        print("🔐 Change password response:", change_response)

        if change_response and change_response.startswith("SUCCESS"):
            flash("✅ Your password has been updated.", "success")
        else:
            flash("❌ Failed to update password.", "error")

    except Exception as e:
        print("⚠️ Exception:", e)
        flash("❌ Invalid or expired confirmation link.", "error")

    return redirect(url_for('profile.profile'))

@profile_bp.route("/invoice/<int:booking_id>")
def download_invoice(booking_id):
        response = send_request(f"GET_INVOICE|{booking_id}")

        status, data = response.split("|", 1)   

        data = json.loads(data)

        scooter = {
            "cost_per_minute": data["cost_per_minute"],
            "make": data["make"],
            "id": data["scooter_id"]
        }

        booking = {
            "checkin_time": data["checkin_time"],
        }


        generate_invoice(scooter, data["checkout_time"], booking, data["total_price"], "./static/logo.png", "./static/rmit.png")

         # Flash a success message
        flash("Invoice downloaded successfully!")

        # Redirect to user history
        return redirect(url_for('user.history'))
