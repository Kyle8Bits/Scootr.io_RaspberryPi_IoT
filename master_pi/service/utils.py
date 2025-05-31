from datetime import datetime
import pytz

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