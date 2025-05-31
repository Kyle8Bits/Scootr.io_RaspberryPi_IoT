from send_socket import send_request
import json
from sense_hat_control import show_status, clear_display
from termcolor import colored
from datetime import datetime
import pytz

def clear_terminal():
    """Clear the terminal screen."""
    print("\033[H\033[J", end="")

def print_colored_message(message, color="green", bold=False):
    """Print a colored and optional bold message."""
    print(colored(message, color, attrs=["bold"] if bold else []))

def get_scooter(scooter_id):
    """Fetch scooter data."""
    response = send_request(f"GET_SCOOTER_BY_ID|{scooter_id}")
    scooter = json.loads(response.split("|")[1])
    return scooter

def update_sense_hat(scooter_id):
    
    matrix = []
    matrix = [(0,0,0)] * 64 
    scooter_data = get_scooter(scooter_id)
    if scooter_data["status"] == "available":
        show_status(0, matrix, (0, 255, 0))
    elif scooter_data["status"] == "booked":
        show_status(1, matrix, (255, 255, 0))
    elif scooter_data["status"] == "in_use":
        show_status(2, matrix, (0, 0, 255))
    elif scooter_data["status"] == "to_be_repaired" or scooter_data["status"] == "under_repair'":
        show_status(3, matrix, (255,0,0))


def if_booked(auth, scooter_data):
    response = send_request(f"HISTORY|{auth}")
    booking_string= response.split("|")[1]
    booking_data = json.loads(booking_string)

    if not booking_data or scooter_data["status"] == 'available':
        return "NOT_BOOKED", None

    for booking in booking_data:
        if str(booking["scooter_id"]) == str(scooter_data["id"]) and booking["status"] in ['waiting', 'in_use']:
            return "BOOKED", booking

    return "NOT_BOOKED", None

def calculate_total_time(time_import, time_now):
    total_hours = 1
    # Parse the date-time strings into datetime objects
    time_import = datetime.strptime(time_import, "%Y-%m-%d %H:%M:%S")
    time_now = datetime.strptime(time_now, "%Y-%m-%d %H:%M")
    
    # Calculate the difference in days
    days_difference = (time_now - time_import).days

    # Calculate the total difference in minutes for the time portion
    total_minutes_now = time_now.hour * 60 + time_now.minute
    total_minutes_import = time_import.hour * 60 + time_import.minute

    # Calculate the total time in minutes for the time difference
    total_time_in_minutes = total_minutes_now - total_minutes_import

    # Convert the total time into hours and handle any remaining minutes
    total_hours = total_time_in_minutes // 60  # This gives the full hours
    remaining_minutes = total_time_in_minutes % 60  # This gives the remaining minutes

    # If there are any remaining minutes greater than 10, round up the hour
    if remaining_minutes > 10:
        total_hours += 1
    
    # Add the day difference in hours to the total hours
    total_hours +=  (days_difference * 24)

    return total_hours


def get_time():
    vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    vietnam_time = datetime.now(vietnam_tz)
    formatted_time = vietnam_time.strftime('%Y-%m-%d %H:%M')

    return formatted_time