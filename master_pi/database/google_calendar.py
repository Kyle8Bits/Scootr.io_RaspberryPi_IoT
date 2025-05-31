from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import datetime
import os
import json
import pytz

# Load the credentials
def load_credentials():
    creds = None

    # Always resolve from parent of current file
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    token_path = os.path.join(base_dir, 'token.json')
    credentials_path = os.path.join(base_dir, 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/calendar'])

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            # This forces Google to show the consent screen again
            creds = flow.run_local_server(port=2222, access_type='offline', prompt='consent')
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds



# Function to create an event
def create_event(email_attendee, event_date, event_time, duration_event, location, detail):
    creds = load_credentials()
    service = build('calendar', 'v3', credentials=creds)

    # Vietnam time zone (Asia/Ho_Chi_Minh)
    local_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    # Parse the date and time
    event_start = datetime.datetime.strptime(f"{event_date} {event_time}", '%Y-%m-%d %H:%M')

    # Localize the start time (convert it from naive datetime to aware datetime in the Vietnam time zone)
    event_start_local = local_tz.localize(event_start)

    # Convert the event start time to UTC (Google Calendar API requires UTC)
    event_start_utc = event_start_local.astimezone(pytz.utc)

    # Calculate the event's end time (assuming it's in the same time zone)
    event_end_utc = event_start_utc + datetime.timedelta(minutes=duration_event)

    # Create the event body
    event = {
        'summary': 'Scooter Booking',
        'location': location,
        'description': detail,
        'start': {
            'dateTime': event_start_utc.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': event_end_utc.isoformat(),
            'timeZone': 'UTC',
        },
        'attendees': [{'email': email_attendee}],
        'reminders': {
            'useDefault': True,
        },
    }

    try:
        # Insert the event into the calendar
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created successfully: {event_result['htmlLink']}")
        return event_result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def delete_event(event_id):
    creds = load_credentials()
    service = build('calendar', 'v3', credentials=creds)

    try:
        # Deleting the event using its ID
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event with ID {event_id} has been deleted.")
    except Exception as e:
        print(f"An error occurred: {e}")


# load_credentials()
# # Example Usage:
# email_attendees = ["example1@gmail.com", "example2@gmail.com"]  # Add email of attendees
# event_date = "2025-05-06"  # Event date in YYYY-MM-DD format
# event_time = "14:00"  # Event start time in HH:MM format
# duration_event = 60  # Duration in minutes
# location = "New York City, Central Park"
# detail = "Scooter booking event to reserve a scooter for rent."


# # # Create event
# create_event(email_attendees, event_date, event_time, duration_event, location, detail)

