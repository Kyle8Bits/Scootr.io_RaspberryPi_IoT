from flask import Blueprint, render_template, request, redirect, url_for, session
from socket_com.send_socket import send_request
import json
from flask import flash
from datetime import datetime
from flask_mail import Mail, Message
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from flask import session, request, flash, redirect, url_for
from passlib.hash import scrypt
import hashlib
from utils.session_utils import update_session_balance
import os


user_bp = Blueprint('user', __name__)
import stripe
stripe.api_key =  os.getenv('STRIPE_API_KEY')
YOUR_DOMAIN = "http://127.0.0.1:5001"

# --------------------------
# LOGIN
# --------------------------
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('login.html', error="❌ Please fill in all fields.")

        response = send_request(f"LOGIN|{username}|{password}")
        status = response.split("|")[0]

        if status == "SUCCESS":
            user = json.loads(response.split("|")[1])
            session['user'] = user['username']
            session['user_id'] = user['id']
            session['balance'] = float(user['balance'])
            session['role'] = user.get('role', 'customer')  # ✅ Save role to session

            print("✅ Login successful. Session:", dict(session))

            # ✅ Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin.admin_home'))
            elif session['role'] == 'engineer':
                return redirect(url_for('engineer.engineer_home'))
            else:
                return redirect(url_for('booking.booking'))

        elif status == "FAILURE":
            return render_template('login.html', error="❌ Invalid username or password.")
        elif status == "NOT_FOUND":
            return render_template('login.html', error="Cannot find your account. Please register.")
        elif status == "ERROR":
            return render_template('login.html', error="❌ An error occurred. Please try again.")

    return render_template('login.html')

# --------------------------
# REGISTER
# --------------------------
@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    mail = Mail(current_app)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm']

        if password != confirm_password:
            return render_template('register.html', error="❗Passwords do not match.")

        response = send_request(f"IF_EXIST|{username}|{email}").strip()
        print("🔐 IF_EXIST response:", response)

        if not response.startswith("SUCCESS"):
            return render_template('register.html', error="⚠️ Username or email already exists.")

        try:
            serializer = URLSafeTimedSerializer(current_app.secret_key)
            token = serializer.dumps({
                "username": username,
                "email": email,
                "password": password
            }, salt='email-verification')

            confirm_url = url_for('user.confirm_email', token=token, _external=True)

            msg = Message("Confirm Your Email", recipients=[email])
            msg.body = f"Click the link to confirm your email: {confirm_url}"
            mail.send(msg)

            return render_template('register.html', success="📩 A verification email has been sent. Please check your inbox.")
        
        except Exception as e:
            print(f"❌ Email error: {e}")
            return render_template('register.html', error="❌ Error sending email")

    return render_template('register.html')

@user_bp.route('/confirm-email/<token>', methods=['GET'])
def confirm_email(token):
    serializer = URLSafeTimedSerializer(current_app.secret_key)

    try:
        data = serializer.loads(token, salt='email-verification', max_age=3600)
        username = data['username']
        email = data['email']
        password = data['password']

        response = send_request(f"REGISTER|{username}|{email}|{password}")
        
        if response.startswith("SUCCESS"):
            return render_template('login.html', success="✅ Your email has been verified. You can now login.")
        else:
            return render_template('register.html', error="❌ Failed to complete registration.")

    except Exception as e:
        print(f"❌ Error: {e}")
        return render_template('register.html', error="❌ Invalid or expired verification link.")

# --------------------------
# LOGOUT
# --------------------------
@user_bp.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('landing'))  # Redirect to homepage after logout


# --------------------------
# History 
# --------------------------

@user_bp.route('/history')
def history():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login'))

    response = send_request(f"HISTORY|{user_id}")
    status, payload = response.split("|", 1)

    if status != "SUCCESS":
        return render_template("history.html", bookings=[])

    bookings = json.loads(payload)

    return render_template("history.html", bookings=bookings)




@user_bp.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login'))

    response = send_request(f"CANCEL_BOOKING|{user_id}|{booking_id}")
    status = response.split("|")[0]

    if status == "SUCCESS":
        flash("✅ Booking successfully canceled", "success")
    else:
        message = response.split("|")[1] if "|" in response else "❌ An error occurred"
        flash(f"❌ {message}", "error")

    return redirect(url_for('user.my_bookings'))

@user_bp.route('/checkin_booking/<int:booking_id>', methods=['POST'])
def checkin_booking(booking_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login'))

    now = datetime.now()
    checkin_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
    response = send_request(f"CHECKIN_BOOKING|{booking_id}|{checkin_datetime}")

    status = response.split("|")[0]

    if status == "SUCCESS":
        flash("🛵 Check-in successful!", "success")
    else:
        message = response.split("|")[1] if "|" in response else "❌ An error occurred during check-in"
        flash(f"❌ {message}", "error")

    return redirect(url_for('user.my_bookings'))




@user_bp.route('/my_bookings')
def my_bookings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login'))

    response = send_request(f"HISTORY|{user_id}")
    status, payload = response.split("|", 1)

    if status != "SUCCESS":
        return render_template("my_bookings.html", bookings=[])

    bookings = json.loads(payload)

    print("Bookings:", bookings)

    # Only show active bookings
    active = [b for b in bookings if b['status'] in ['waiting', 'in-use']]

    return render_template("my_bookings.html", bookings=active)

# --------------------------
# Top Up (Stripe Checkout)
# --------------------------

@user_bp.route('/top-up')
def top_up():
    if 'user_id' not in session:
        return redirect(url_for('user.login', error="❗Session expired. Please login again."))


    amount = request.args.get('amount')
    if not amount or not amount.isdigit() or int(amount) <= 0:
        return redirect(url_for('profile.profile', error="❌ Invalid top-up amount."))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(amount) * 100,  # Stripe wants cents
                    'product_data': {'name': f"Top-Up ${amount}"}
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url="http://127.0.0.1:5001/top-up-complete?amount=" + str(amount),
            cancel_url="http://127.0.0.1:5001/profile",

        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        print(f"❌ Stripe Error: {e}")
        return redirect(url_for('profile.profile', error="❌ Payment initialization failed."))



# --------------------------
# After Stripe Payment Success
# --------------------------

@user_bp.route('/top-up-complete')
def top_up_complete():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('user.login', error="❗Session expired. Please login again."))

    amount = request.args.get('amount')
    if not amount or not amount.isdigit():
        return redirect(url_for('profile.profile', error="⚠️ Payment completed, but invalid amount received."))

    try:
        response = send_request(f"TOP_UP|{user_id}|{amount}")
        if response.startswith("SUCCESS"):
            if update_session_balance(user_id):
                return redirect(url_for('profile.profile', success=f"✅ Successfully topped up ${amount}!"))
            else:
                return redirect(url_for('profile.profile', error="⚠️ Top-up succeeded, but failed to fetch updated balance."))
        else:
            return redirect(url_for('profile.profile', error="❌ Top-up failed after payment. Please contact support."))

    except Exception as e:
        print(f"❌ Error during top-up completion: {e}")
        return redirect(url_for('profile.profile', error="❌ Unexpected error after payment."))

# --------------------------
# CHANGE PASSWORD
# --------------------------
@user_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    mail = Mail(current_app)

    if request.method == 'GET':
        return render_template('change_password.html')

    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            return render_template('change_password.html', error="❌ New passwords do not match")

        response = send_request(f"GET_USER_ID_BY_EMAIL|{email}").strip()

        if not response or not response.startswith("SUCCESS|"):
            return render_template('change_password.html', error="⚠️ Account with the entered EMAIL does not exist in the system.")

        parts = response.split("|", 1)
        if len(parts) < 2:
            return render_template('change_password.html', error="❌ Unexpected server response.")

        user_id = parts[1]

        try:
            serializer = URLSafeTimedSerializer(current_app.secret_key)
            token = serializer.dumps({
                "user_id": user_id,
                "password": hashlib.sha256(new_password.encode()).hexdigest()
            }, salt='password-change')

            confirm_url = url_for('user.confirm_password_change', token=token, _external=True)

            msg = Message("Confirm Your Password Change", recipients=[email])
            msg.body = f"Click the link to confirm your password change: {confirm_url}"

            mail.send(msg)
            return render_template('login.html', success="📩 A verification email has been sent. Please check your inbox.")

        except Exception as e:
            print(f"❌ Email error: {e}")
            return render_template('login.html', error="❌ Error sending email.")

    return render_template('login.html')


# --------------------------
# CONFIRM PASSWORD CHANGE
# --------------------------
@user_bp.route('/user/confirm_password_change/<token>')
def confirm_password_change(token):
    serializer = URLSafeTimedSerializer(current_app.secret_key)

    try:
        data = serializer.loads(token, salt='password-change', max_age=3600)
        user_id = data['user_id']
        new_hash = data['password']

        payload = f"CHANGE_PASSWORD|{user_id}|{new_hash}"
        change_response = send_request(payload)
        print("🔐 Change password response:", change_response)

        if change_response and change_response.startswith("SUCCESS"):
            return render_template('login.html', success="✅ Your password has been updated.")
        else:
            return render_template('login.html', error="❌ Failed to update password.")

    except Exception as e:
        print("⚠️ Exception:", e)
        return render_template('login.html', error="❌ Invalid or expired confirmation link.")
