"""
BookingService.py

Service module for handling all booking-related operations.

This includes booking creation, check-in/check-out logic,
cancellation handling, refund processing, and calendar integration
via Google Calendar.

Functions use utility helpers like:
- `get_by_field`, `update_field`, `add_into_table` for DB operations.
- `create_event`, `delete_event` for calendar syncing.

All functions assume bookings cost 10 units as a base rate.

Classes:
    Booking: Contains static methods to handle booking lifecycle operations.
"""

from ..database.db_connect import db_connect as get_db
from .ScooterService import Scooter
import requests
from .ReportService import Report
from .UserService import User 
from ..database.google_calendar import create_event, delete_event
import datetime
import pytz
import json
from dotenv import load_dotenv
import os
from .crud import get_by_field, update_field, add_into_table, get_all_from_table
import decimal 
from collections import defaultdict

class Booking:
    """
    The Booking class handles the full booking lifecycle:
    create, cancel, check-in, and check-out.
    """

    @staticmethod
    def create_booking(user_id, scooter_id, date, checkin_time):
        """
        Create a new booking for a scooter.

        Checks user balance and scooter availability, reserves the scooter,
        deducts balance, creates a calendar event, and inserts a new booking.

        Args:
            user_id (int): The ID of the user making the booking.
            scooter_id (int): The ID of the scooter being booked.
            date (str): Date of booking.
            checkin_time (str): Expected check-in time.

        Returns:
            str: "SUCCESS", "INSUFFICIENT_BALANCE", or "ERROR|<details>".
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            scooter = get_by_field(cursor, "scooters", "id", scooter_id, "one")
            user = get_by_field(cursor, "users", "id", user_id, "one")

            if not scooter or not user:
                return "ERROR|User or scooter not found"

            if user["balance"] < 10:
                return "INSUFFICIENT_BALANCE"

            # Get location name from zones table
            cursor.execute("SELECT name FROM zones WHERE id = %s", (scooter["zone_id"],))
            zone = cursor.fetchone()
            zone_name = zone["name"] if zone else "Unknown Location"

            # Update scooter status to booked
            update_field(cursor, "scooters", {"status": "booked"}, scooter_id)

            # Deduct 10 units from user balance
            update_field(cursor, "users", {"balance": user["balance"] - 10}, user_id)

    

            # Setup calendar event attendees
            user_email = user["email"]
            email_attendees = [user_email, "iot.programming2025@gmail.com"]

            # Create calendar event
            event_id = create_event(
                email_attendees,
                date,
                checkin_time,
                10,
                zone_name,  # ✅ Correct location
                "Scooter booking event to reserve a scooter for rent."
            )

            print("📅 Event created with ID:", event_id["id"])

            # Create booking in DB
            data = {
                'user_id': user_id,
                'scooter_id': scooter_id,
                'rent_date':  f"{date} {checkin_time}",
                'total_price': 0,
                'event_id': event_id["id"],
                'status': "waiting"
            }

            add_into_table(cursor, "bookings", data)
            conn.commit()

            return "SUCCESS"

        except Exception as e:
            print("ERROR|" + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def cancel_booking(user_id, booking_id):
        """
        Cancel an existing booking and refund balance.

        Args:
            user_id (int): User ID to refund.
            booking_id (int): Booking to cancel.

        Returns:
            str: "SUCCESS", "FAILURE", or "ERROR|<details>".
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            booking = get_by_field(cursor, "bookings", "id", booking_id, "one")
            if not booking:
                return "FAILURE"

            # Mark booking as canceled
            update_field(cursor, "bookings", {"status": "canceled"}, booking_id)

            # Return scooter to available
            update_field(cursor, "scooters", {"status": "available"}, booking["scooter_id"])

            # Refund 10 to user
            User.top_up(user_id, 10)

            # Delete event from calendar if exists
            if booking.get("event_id"):
                delete_event(booking["event_id"])

            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def checkin_booking(booking_id, checking_time):
        """
        Update booking and scooter status on check-in.

        Args:
            booking_id (int): Booking ID.
            checking_time (str): Actual check-in time.
            checkin_date (str): Actual check-in date.

        Returns:
            str: "SUCCESS" or error string.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            booking = get_by_field(cursor, "bookings", "id", booking_id, "one")
            if not booking:
                return "ERROR|Booking not found"

            update_field(cursor, "bookings", {
                "status": "in_use",
                "checkin_time": checking_time,
            }, booking_id)

            update_field(cursor, "scooters", {"status": "in_use"}, booking["scooter_id"])

            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def checkout_booking(booking_id, checkout_time, total_price):
        """
        Handle booking checkout and adjust balances.

        Args:
            booking_id (int): Booking ID.
            checkout_time (str): Time of checkout.
            total_price (float or str): Final cost of the booking.

        Returns:
            str: "SUCCESS" or "INSUFFICIENT_BALANCE"
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            booking = get_by_field(cursor, "bookings", "id", booking_id, "one")
            if not booking:
                return "ERROR|Booking not found"

            user = get_by_field(cursor, "users", "id", booking["user_id"], "one")
            if not user:
                return "ERROR|User not found"

            total_price = float(total_price)

            # 💡 Balance logic FIRST before updates
            if total_price <= 10:
                refund = 10 - total_price
                User.top_up(user["id"], refund)
            elif user["balance"] >= (total_price - 10):
                extra = total_price - 10
                User.top_up(user["id"], -extra)
            else:
                return "INSUFFICIENT_BALANCE"

            # ✅ Proceed with updates after successful balance check
            update_field(cursor, "bookings", {
                "status": "returned",
                "checkout_date": checkout_time,
                "total_price": total_price
            }, booking_id)

            cursor.execute("""
                SELECT TIMESTAMPDIFF(MINUTE, checkin_time, checkout_date) AS minutes_diff
                FROM bookings
                WHERE id = %s
            """, (booking_id,))

            minute_use = cursor.fetchone()["minutes_diff"]

            cursor.execute("""
                SELECT power_remaining
                FROM scooters
                WHERE id = %s
            """, (booking["scooter_id"],))

            scooter = cursor.fetchone()

            zone = get_by_field(cursor, "zones", "id", scooter["zone_id"], "one")

            power_used = 0
            current_power = scooter["power_remaining"]

            if minute_use and minute_use > 0:
                power_used = minute_use * 0.1
                new_power = current_power - power_used
                if new_power < 0:
                    new_power = 0

            if new_power <= 10 and new_power >= 0:
                load_dotenv()
                api_key = os.getenv("GOOGLE_MAPS_API_KEY")
                lat, lng = get_place_location(zone, api_key)
                Report.report_issue(user["id"], booking["scooter_id"], "Out of Power", "Battery is low, please recharge.", lat, lng)
                update_field(cursor, "scooters", {"status": "to_be_repaired"}, booking["scooter_id"])
            elif new_power > 10:
                update_field(cursor, "scooters", {"status": "available"}, booking["scooter_id"])
                Scooter.update_scooter_power(booking["scooter_id"],new_power)

                
            # Update scooter status to available
            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_invoice(booking_id):
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            booking = get_by_field(cursor, "bookings", "id", booking_id, "one")
            scooter = get_by_field(cursor, "scooters", "id", booking["scooter_id"], "one")

            # Convert datetime objects to strings
            checkin_time_str = booking["checkin_time"].strftime('%Y-%m-%d %H:%M:%S') if booking["checkin_time"] else None
            checkout_time_str = booking["checkout_date"].strftime('%Y-%m-%d %H:%M:%S') if booking["checkout_time"] else None

            price = float(booking["total_price"])
            cost_per_minute = float(scooter["cost_per_minute"])

            data = {
                "checkin_time": checkin_time_str,
                "checkout_date": checkout_time_str,
                "total_price": price,
                "make": scooter["make"],
                "cost_per_minute": cost_per_minute,
                "scooter_id": scooter["id"],
            }

            response = json.dumps(data)
            return f"SUCCESS|{response}"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_all_bookings():
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    b.id AS booking_id,
                    u.username,
                    s.make AS scooter_make,
                    b.status,
                    b.rent_date,
                    b.checkin_time,
                    b.checkout_date AS checkout_time,
                    b.total_price
                FROM bookings b
                LEFT JOIN users u ON b.user_id = u.id
                LEFT JOIN scooters s ON b.scooter_id = s.id
            """)
            rows = cursor.fetchall()

            for row in rows:
                for key in ["rent_date", "checkin_time", "checkout_time"]:
                    if row[key] and isinstance(row[key], datetime.datetime):
                        row[key] = row[key].strftime('%Y-%m-%d %H:%M:%S')

            return f"SUCCESS|{json.dumps(rows, default=decimal_default)}"

        except Exception as e:
            print("❌ get_all_bookings error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor: cursor.close()
            if conn: conn.close()




    @staticmethod
    def get_user_booking_count(user_id):
        """
        Returns the total number of bookings made by a specific user.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM bookings WHERE user_id = %s
            """, (user_id,))
            result = cursor.fetchone()

            count = result[0] if result else 0
            return f"SUCCESS|{count}"
        except Exception as e:
            print("❌ get_user_booking_count error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    @staticmethod
    def get_usage_analytics(mode):
        """
        Return scooter usage grouped by day or week.

        Returns:
            SUCCESS|{ "labels": [...], "values": [...], "total_rides": int, "total_revenue": float }
            or FAILURE|error
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    DATE(checkout_date) AS day,
                    WEEK(checkout_date, 1) AS week,
                    total_price
                FROM bookings
                WHERE status = 'returned'
            """)
            rows = cursor.fetchall()

            from collections import defaultdict
            grouped = defaultdict(float)
            total_rides = 0
            total_revenue = 0.0

            for row in rows:
                key = str(row["day"]) if mode == "daily" else f"Week {row['week']}"
                grouped[key] += 1
                total_rides += 1
                total_revenue += float(row["total_price"] or 0)

            labels = sorted(grouped.keys(), key=lambda x: x)
            values = [grouped[k] for k in labels]

            result = {
                "labels": labels,
                "values": values,
                "total_rides": total_rides,
                "total_revenue": round(total_revenue, 2)
            }

            return f"SUCCESS|{json.dumps(result)}"

        except Exception as e:
            print(f"❌ get_usage_analytics error: {e}")
            return f"FAILURE|{str(e)}"

        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    @staticmethod
    def get_top_scooters():
        """
        Returns top scooters by number of completed rides (status = 'returned').
        Output format:
        SUCCESS|[{"scooter_id": 3, "rides": 12}, ...]
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT scooter_id, COUNT(*) AS rides
                FROM bookings
                WHERE status = 'returned'
                GROUP BY scooter_id
                ORDER BY rides DESC
                LIMIT 5
            """)

            rows = cursor.fetchall()
            return f"SUCCESS|{json.dumps(rows)}"

        except Exception as e:
            print("❌ get_top_scooters error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError

def get_place_location(place_name, api_key):
    """
    Given a place name, return its latitude and longitude using Google Maps Places API.
    """
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    
    params = {
        "input": place_name,
        "inputtype": "textquery",
        "fields": "geometry",
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    # Check if any candidates returned
    if data.get("candidates"):
        location = data["candidates"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        raise ValueError(f"Location not found for '{place_name}'")