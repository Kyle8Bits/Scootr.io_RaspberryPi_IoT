# =========================
# Imports and Setup
# =========================
from flask import Blueprint, jsonify, render_template, session, redirect, url_for, request
from flask_mail import Message
from socket_com.send_socket import send_request
import json
from utils.session_utils import mail

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# =========================
# Admin Role Check
# =========================
def _is_admin():
    return session.get('role') == 'admin'

# =========================
# Helper Function
# =========================
def safe_unpack(response):
    parts = response.split("|", 1)
    if len(parts) == 1:
        return parts[0], ""  # Handle responses like "SUCCESS"
    return parts[0], parts[1]



# =========================
# Dashboard
# =========================

@admin_bp.route('/home')
def admin_home():
    if not _is_admin():
        return redirect(url_for('user.login'))
    return render_template("admin/admin_home.html")

# --- Analytics API ---
@admin_bp.route('/analytics')
def admin_analytics_api():
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    view = request.args.get("view", "daily").lower()
    print(f"[🔍 Requested analytics view]: {view}")

    try:
        raw_response = send_request(f"GET_ANALYTICS|{view.upper()}")
        print(f"[📡 Raw socket response]: {raw_response}")

        status, payload = safe_unpack(raw_response)

        if status == "SUCCESS":
            parsed = json.loads(payload)
            parsed.setdefault("labels", [])
            parsed.setdefault("values", [])
            parsed.setdefault("total_rides", 0)
            parsed.setdefault("total_revenue", 0.0)
            return jsonify(parsed)
        else:
            print(f"[❌ Analytics fetch failed] Status: {status}")
            return jsonify(error="Analytics fetch failed"), 500

    except Exception as e:
        print(f"[🔥 Exception in admin_analytics_api]: {e}")
        return jsonify(error=str(e)), 500

    
@admin_bp.route('/metrics')
def admin_metrics():
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    try:
        # Fetch all users and scooters
        status_u, payload_u = safe_unpack(send_request("GET_ALL_USERS|customer"))
        status_s, payload_s = safe_unpack(send_request("GET_ALL_SCOOTER"))

        customers = json.loads(payload_u) if status_u == "SUCCESS" else []
        scooters = json.loads(payload_s) if status_s == "SUCCESS" else []

        return jsonify({
            "customers": len(customers),
            "scooters": len(scooters)
        })

    except Exception as e:
        print("❌ Metrics Error:", e)
        return jsonify(error=str(e)), 500

@admin_bp.route('/top_scooters')
def top_scooters_api():
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    try:
        response = send_request("GET_TOP_SCOOTERS")
        status, payload = safe_unpack(response)

        if status == "SUCCESS":
            data = json.loads(payload)
            # Expecting list of {"scooter_id": ..., "rides": ...}
            top = sorted(data, key=lambda x: x['rides'], reverse=True)[:5]
            labels = [f"Scooter #{s['scooter_id']}" for s in top]
            values = [s['rides'] for s in top]
            return jsonify(labels=labels, values=values)

        return jsonify(labels=[], values=[])

    except Exception as e:
        print(f"[Top Scooters Error] {e}")
        return jsonify(error=str(e)), 500


# =========================
# Scooter Management
# =========================
    
# --- Scooter View Page ---
@admin_bp.route('/scooters')
def admin_view_scooters():
    if not _is_admin():
        return redirect(url_for('user.login'))

    try:
        status_s, payload_s = safe_unpack(send_request("GET_ALL_SCOOTER"))
        status_z, payload_z = safe_unpack(send_request("GET_ALL_ZONES"))
        scooters = json.loads(payload_s) if status_s == "SUCCESS" else []
        zones = json.loads(payload_z) if status_z == "SUCCESS" else []
        return render_template("admin/admin_view_scooters.html", scooters=scooters, zones=zones)
    except Exception as e:
        print(f"[Scooter View Error] {e}")
        return render_template("admin/admin_view_scooters.html", scooters=[], zones=[], error=str(e))



# --- Add Scooter ---
@admin_bp.route('/scooters/add', methods=['POST'])
def admin_add_scooter():
    if not _is_admin():
        return jsonify(success=False, error="Forbidden"), 403

    f = request.form
    if not f.get('zone_id', '').isdigit():
        return jsonify(success=False, error="Invalid zone"), 400

    cmd = "|".join(["ADD_SCOOTER",
                    f.get('make',''),
                    f.get('color',''),
                    f.get('zone_id',''),
                    f.get('battery',''),
                    f.get('cost',''),
                    f.get('status','')])
    try:
        status, _ = safe_unpack(send_request(cmd))
        return jsonify(success=(status == "SUCCESS")), (200 if status == "SUCCESS" else 400)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500



# --- Edit Scooter (GET + POST) ---
@admin_bp.route('/scooters/edit/<int:id>', methods=['POST'])
def admin_edit_scooter(id):
    if not _is_admin():
        return jsonify(success=False, error="Forbidden"), 403

    f = request.form
    if not f.get('zone_id', '').isdigit():
        return jsonify(success=False, error="Invalid zone"), 400

    cmd = "|".join(["EDIT_SCOOTER", str(id),
                    f.get('make',''),
                    f.get('color',''),
                    f.get('zone_id',''),
                    f.get('battery',''),
                    f.get('cost',''),
                    f.get('status','')])
    try:
        status, _ = safe_unpack(send_request(cmd))
        return jsonify(success=(status == "SUCCESS")), (200 if status == "SUCCESS" else 400)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# --- Delete Scooter ---
@admin_bp.route('/scooters/delete/<int:id>', methods=['POST'])
def admin_delete_scooter(id):
    if not _is_admin():
        return redirect(url_for('user.login'))
    try:
        status, _ = safe_unpack(send_request(f"DELETE_SCOOTER|{id}"))
    except Exception as e:
        print(f"[Scooter Delete Error] {e}")
    return redirect(url_for('admin.admin_view_scooters'))


# --- Scooter API (for edit modal) ---
@admin_bp.route('/scooters/api/<int:id>')
def admin_scooter_api(id):
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    try:
        status, payload = safe_unpack(send_request(f"GET_SCOOTER_BY_ID|{id}"))
        if status == "SUCCESS":
            return jsonify(json.loads(payload))
        return jsonify(error="Not found"), 404
    except Exception as e:
        return jsonify(error=str(e)), 500



# =========================
# Usage History Management
# =========================
@admin_bp.route('/usage_history')
def admin_view_bookings():
    if not _is_admin():
        return redirect(url_for('user.login'))

    raw_response = send_request("GET_ALL_BOOKINGS")
    print("📩 Raw socket response:", raw_response)

    try:
        status, payload = raw_response.split("|", 1)
        if status == "SUCCESS":
            bookings = json.loads(payload)
            print(f"✅ Loaded {len(bookings)} bookings")
        else:
            print("❌ Failed to fetch bookings:", status)
            bookings = []
    except Exception as e:
        print("❌ Exception while parsing bookings:", e)
        bookings = []

    return render_template("admin/admin_usage_history.html", bookings=bookings)

# =========================
# User Management
# =========================
@admin_bp.route('/users')
def admin_view_users():
    if not _is_admin():
        return redirect(url_for('user.login'))

    role = request.args.get('role', 'all').upper()
    status, payload = send_request(f"GET_ALL_USERS|{role}").split("|", 1)
    users = json.loads(payload) if status == "SUCCESS" and payload else []
    return render_template("admin/admin_view_users.html", users=users, role=role.lower())


@admin_bp.route('/users/add', methods=['POST'])
def admin_add_user():
    if not _is_admin():
        return jsonify(success=False, error="Forbidden"), 403

    f = request.form
    cmd = "|".join([
        "ADD_USER", f.get('role', '').lower(), f.get('username', ''), f.get('email', ''), f.get('password', ''),
        f.get('first_name', ''), f.get('last_name', ''), f.get('phone_number', '')
    ])
    status = send_request(cmd).split("|", 1)[0]
    success = (status == "SUCCESS")
    return jsonify(success=success), (200 if success else 400)


@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
def admin_edit_user(id):
    if not _is_admin():
        return jsonify(success=False, error="Forbidden"), 403

    if request.method == 'POST':
        data = {
            "first_name": request.form.get('first_name', ''),
            "last_name": request.form.get('last_name', ''),
            "phone_number": request.form.get('phone_number', '')
        }
        cmd = f"EDIT_USER|{id}|{json.dumps(data)}"
        status = send_request(cmd).split("|", 1)[0]
        success = (status == "SUCCESS")
        return jsonify(success=success), (200 if success else 400)

    raw = send_request(f"GET_USER_DETAILS|{id}")
    status, payload = raw.split("|", 1) if "|" in raw else (raw, "")
    user = json.loads(payload) if status == "SUCCESS" and payload else {}
    return render_template("admin/edit_user.html", user=user)


@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
def admin_delete_user(id):
    if not _is_admin():
        return redirect(url_for('user.login'))

    send_request(f"DELETE_USER|{id}")
    return redirect(url_for('admin.admin_view_users'))


@admin_bp.route('/users/api/<int:id>')
def admin_user_api(id):
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    status, payload = send_request(f"GET_USER_DETAILS|{id}").split("|", 1)
    if status == "SUCCESS" and payload:
        return jsonify(json.loads(payload))
    return jsonify(error="User not found"), 404


@admin_bp.route('/users/view/<int:id>')
def admin_view_user_card(id):
    if not _is_admin():
        return redirect(url_for('user.login'))

    status, payload = send_request(f"GET_USER_DETAILS|{id}").split("|", 1)
    if status == "SUCCESS":
        user = json.loads(payload)
        return render_template("admin/view_user_card.html", user=user)

    return render_template("admin/view_user_card.html", user=None, error="User not found")


@admin_bp.route('/users/<int:id>/report_count')
def get_report_count(id):
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    status, payload = send_request(f"GET_USER_REPORT_COUNT|{id}").split("|", 1)
    return jsonify(count=int(payload)) if status == "SUCCESS" else jsonify(count=0)


@admin_bp.route('/users/<int:id>/booking_count')
def get_booking_count(id):
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    status, payload = send_request(f"GET_USER_BOOKING_COUNT|{id}").split("|", 1)
    return jsonify(count=int(payload)) if status == "SUCCESS" else jsonify(count=0)


# =========================
# Issue Management
# =========================
@admin_bp.route('/issues')
def admin_view_issues():
    if not _is_admin():
        return redirect(url_for('user.login'))

    return render_template("admin/admin_issues.html")


@admin_bp.route('/issues/api')
def admin_issues_api():
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    try:
        status, payload = send_request("GET_ALL_ISSUES").split("|", 1)
        if status == "SUCCESS":
            issues = json.loads(payload)
            return jsonify(issues)
        return jsonify(error="Failed to load issues"), 500
    except Exception as e:
        return jsonify(error="Exception occurred", details=str(e)), 500


@admin_bp.route('/issues/approve/<int:issue_id>', methods=['POST'])
def approve_issue(issue_id):
    try:
        approve_response = send_request(f"APPROVE_ISSUE|{issue_id}")
        if not approve_response.startswith("SUCCESS"):
            return jsonify({"success": False, "error": "Failed to approve issue."})

        issue_response = send_request(f"GET_ISSUE_BY_ID|{issue_id}")
        if not issue_response.startswith("SUCCESS"):
            return jsonify({"success": False, "error": "Issue not found."})

        issue = json.loads(issue_response.split("|", 1)[1])
        email_response = send_request("GET_ALL_ENGINEERS_EMAIL")
        if not email_response.startswith("SUCCESS"):
            return jsonify({"success": False, "error": "Could not get engineer emails."})

        engineer_emails = json.loads(email_response.split("|", 1)[1])

        try:
            msg = Message(
                subject=f"🛠 New Approved Issue Report - ID #{issue['id']}",
                recipients=engineer_emails,
                body=f"""
Hello Engineer,

A new scooter issue has been approved. Please find the details below:

🆔 Issue ID: {issue['id']}
🛴 Scooter ID: {issue['scooter_id']}
📅 Reported At: {issue['reported_at']}
📌 Status: {issue['status']}
⚠️ Issue Type: {issue['issue_type']}
📝 Details: {issue['additional_details'] or 'N/A'}
📍 Location Coordinates: ({issue['latitude']}, {issue['longitude']})

Please take the necessary actions.

- Scootr.io System
"""
            )
            mail.send(msg)
        except Exception as e:
            print("❌ Failed to send email:", e)

        return jsonify({"success": True})

    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


# =========================
# Top-Up History (Admin)
# =========================

@admin_bp.route('/topups')
def admin_view_topups():
    if not _is_admin():
        return redirect(url_for('user.login'))
    return render_template("admin/admin_topups.html")

@admin_bp.route('/topups/api')
def admin_topups_api():
    if not _is_admin():
        return jsonify(error="Forbidden"), 403

    try:
        raw = send_request("GET_ALL_TOPUPS")
        status, payload = safe_unpack(raw)

        if status == "SUCCESS":
            topups = json.loads(payload)
            return jsonify(topups)
        else:
            return jsonify(error="Failed to load top-up history"), 500

    except Exception as e:
        print(f"[❌ Top-Up API Error] {e}")
        return jsonify(error="Server error", details=str(e)), 500
