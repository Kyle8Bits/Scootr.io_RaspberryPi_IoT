import json
from flask import Blueprint, current_app, flash, jsonify, render_template, request, session, redirect, url_for
from socket_com.send_socket import send_request
from .qr_scanner import open_scanner
from collections import Counter
import traceback
from datetime import datetime
engineer_bp = Blueprint('engineer', __name__)

@engineer_bp.route('/engineer/engineer_home')
def engineer_home():
    if session.get('role') != 'engineer':
        return redirect(url_for('user.login'))

    return render_template('engineer/engineer_home.html')

@engineer_bp.route("/engineer/home/api")
def engineer_dashboard_data():
    if session.get("role") != "engineer":
        return jsonify(error="Unauthorized"), 403

    engineer_id = session.get("user_id")

    try:
        # Fetch assigned issues
        response_issues = send_request(f"GET_ENGINEER_ISSUES|{engineer_id}")
        status_issues, payload_issues = response_issues.split("|", 1)
        assigned_issues = json.loads(payload_issues) if status_issues == "SUCCESS" else []

        # Fetch resolved issues
        response_resolved = send_request(f"GET_ENGINEER_RESOLVED_ISSUES|{engineer_id}")
        status_resolved, payload_resolved = response_resolved.split("|", 1)
        resolved_issues = json.loads(payload_resolved) if status_resolved == "SUCCESS" else []

        # Count statuses
        status_counter = Counter(issue["status"] for issue in assigned_issues)

        # Battery info
        assigned_scooter_ids = list({issue["scooter_id"] for issue in assigned_issues})
        battery_levels = []
        for scooter_id in assigned_scooter_ids:
            scooter_res = send_request(f"GET_SCOOTER_BY_ID|{scooter_id}")
            if scooter_res.startswith("SUCCESS"):
                scooter_data = json.loads(scooter_res.split("|", 1)[1])
                battery = scooter_data.get("power_remaining")
                if isinstance(battery, (int, float)):
                    battery_levels.append(battery)

        avg_battery = round(sum(battery_levels) / len(battery_levels), 2) if battery_levels else 0
        lowest_battery = min(battery_levels) if battery_levels else 0

        # Resolution time formatting
        def parse_time(ts):
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") if ts and ts != "None" else None

        def format_minutes_as_hm(minutes):
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            if hours > 0:
                return f"{hours}h {mins}m"
            return f"{mins}m"

        resolution_durations = []
        for res in resolved_issues:
            start = parse_time(res.get("approved_at"))
            end = parse_time(res.get("resolved_at"))
            if start and end:
                diff_minutes = abs((end - start).total_seconds()) / 60
                resolution_durations.append(diff_minutes)

        if resolution_durations:
            avg_minutes = sum(resolution_durations) / len(resolution_durations)
            avg_resolution_time = format_minutes_as_hm(avg_minutes)
        else:
            avg_resolution_time = "N/A"

        recent_resolutions = sorted(resolved_issues, key=lambda r: r.get("resolved_at", ""), reverse=True)[:5]

        return jsonify({
            "assigned_scooters": len(assigned_scooter_ids),
            "resolved_issues": len(resolved_issues),
            "average_battery": avg_battery,
            "lowest_battery": lowest_battery,
            "average_resolution_time": avg_resolution_time,
            "status_counts": dict(status_counter),
            "recent_resolutions": recent_resolutions
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(error="Server error", details=str(e)), 500
    

@engineer_bp.route('/engineer/map')
def map_view():
    return render_template(
        'engineer/map_view.html',
        google_maps_api_key=current_app.config["GOOGLE_MAPS_API_KEY"]
    )

@engineer_bp.route('/engineer/map/issues')
def get_issues_for_map():
    try:
        response = send_request("GET_ALL_APPROVE_ISSUES_DETAILS")
        # print("🧪 Response:", response)  # Add debug print
        status, payload = response.split("|", 1)
        if status == "SUCCESS":
            issues = json.loads(payload)
            return jsonify(issues)
        return jsonify(error="Failed to load issues"), 500
    except Exception as e:
        return jsonify(error="Exception occurred", details=str(e)), 500

@engineer_bp.route('/engineer/issue')
def issue_detail():
    issue_id = request.args.get("issue_id", type=int)
    scooter_id = request.args.get("scooter_id", type=int)

    if not issue_id or not scooter_id:
        return "Missing issue_id or scooter_id", 400

    try:
        # Fetch issue by ID
        issue_res = send_request(f"GET_ISSUE_BY_ID|{issue_id}")

        if not issue_res.startswith("SUCCESS"):
            raise Exception("Issue not found")
        issue = json.loads(issue_res.split("|", 1)[1])

        # Fetch scooter by ID
        scooter_res = send_request(f"GET_SCOOTER_BY_ID|{scooter_id}")
        if not scooter_res.startswith("SUCCESS"):
            raise Exception("Scooter not found")
        scooter = json.loads(scooter_res.split("|", 1)[1])

        return render_template("engineer/issue_detail.html", issue=issue, scooter=scooter)

    except Exception as e:
        return f"Error loading issue details: {str(e)}", 500

@engineer_bp.route('/engineer/issue/claim', methods=['POST'])
def claim_issue():
    if session.get('role') != 'engineer':
        return redirect(url_for('user.login'))
    user_id = session.get('user_id')
    issue_id = request.form.get('issue_id', type=int)
    
    if not issue_id:
        return jsonify({"success": False, "error": "Missing issue_id."}), 400

    response = send_request(f"ENGINEER_CLAIM_ISSUE|{issue_id}|{user_id}")
    if not response.startswith("SUCCESS"):
        return jsonify({"success": False, "error": "Issue not found or claim failed."})

    return jsonify({"success": True, "message": "Issue successfully claimed by engineer."})


@engineer_bp.route('/engineer/issues/api')
def engineer_issues_api():
    if session.get('role') != 'engineer':
        return jsonify(error="Forbidden"), 403

    engineer_id = session.get('user_id')
    try:
        response = send_request(f"GET_ENGINEER_ISSUES|{engineer_id}")
        status, payload = response.split("|", 1)

        if status == "SUCCESS":
            return jsonify(json.loads(payload))
        return jsonify(error="Failed to fetch assigned issues"), 500

    except Exception as e:
        return jsonify(error="Backend error", details=str(e)), 500


@engineer_bp.route("/engineer/issues/<int:issue_id>/resolve", methods=["POST"])
def resolve_engineer_issue(issue_id):
    if session.get("role") != "engineer":
        return jsonify(success=False, error="Unauthorized"), 403

    data = request.get_json()
    resolution_type = data.get("resolution_type", "").strip()
    resolution_details = data.get("resolution_details", "").strip()

    if not resolution_details:
        return jsonify(success=False, error="Resolution details required"), 400

    engineer_id = session.get("user_id")

    # Format: ENGINEER_MARK_RESOLVED|<issue_id>|<engineer_id>|<type>|<details>
    cmd = f"ENGINEER_MARK_RESOLVED|{issue_id}|{engineer_id}|{resolution_type}|{resolution_details}"
    response = send_request(cmd)

    return jsonify(success=response.startswith("SUCCESS"), error=None if response.startswith("SUCCESS") else response)


@engineer_bp.route('/engineer/report')
def engineer_report_results():
    if session.get('role') != 'engineer':
        return redirect(url_for('user.login'))

    return render_template("engineer/engineer_report_results.html")

@engineer_bp.route('/engineer/report/api')
def get_engineer_resolved_issues():
    if session.get('role') != 'engineer':
        return jsonify(error="Forbidden"), 403

    engineer_id = session.get('user_id')

    try:
        response = send_request(f"GET_ENGINEER_RESOLVED_ISSUES|{engineer_id}")
        status, payload = response.split("|", 1)

        if status == "SUCCESS":
            issues = json.loads(payload)
            return jsonify(issues)
        return jsonify(error="Failed to fetch resolved issues"), 500

    except Exception as e:
        return jsonify(error="Server error", details=str(e)), 500
    

@engineer_bp.route('/engineer/scooters')
def engineer_view_issues():
    if session.get('role') != 'engineer':
        return redirect(url_for('user.login'))
    return render_template('engineer/engineer_issues.html')


@engineer_bp.route('/engineer/scooter/<int:scooter_id>')
def engineer_get_scooter(scooter_id):
    if session.get('role') != 'engineer':
        return jsonify(error="Forbidden"), 403

    try:
        # This sends scooter_id as a string, which is fine now
        response = send_request(f"GET_SCOOTER_BY_ID|{scooter_id}")
        status, payload = response.split("|", 1) if "|" in response else (response, "")

        if status == "SUCCESS":
            return jsonify(json.loads(payload))
        else:
            return jsonify(error="Scooter not found"), 404

    except Exception as e:
        print("❌ Error in /engineer/scooter/<id>:", e)
        return jsonify(error="Server error", details=str(e)), 500

