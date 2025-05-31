import hashlib
from ..database.db_connect import db_connect as get_db# DB connection alias
from decimal import Decimal  # For handling monetary values
from datetime import datetime
from flask import session
import json
from .crud import get_by_field, update_field, add_into_table
from .utils import get_time, calculate_total_time

class User:

    """
    Handles user-related operations including authentication,
    profile management, balance top-ups, and booking history.
    """
    @staticmethod
    def login(username, password):

        """
        Authenticate a user with username and password.

        Args:
            username (str): The username.
            password (str): The password to check (in plain text).

        Returns:
            str: JSON response string with user data on success,
                 "FAILURE" on incorrect password,
                 or "NOT_FOUND" if user does not exist.
        """
        try:
            # Get DB connection
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            # Get user data by username
            user = get_by_field(cursor, "users", "username", username, "one")
            
            if user:
                # Verify password hash using scrypt
                if hashlib.sha256(password.encode()).hexdigest() == user['password_hash']:
                    # Successfully authenticated, return user data
                    user_data = {
                        'username': user['username'],
                        'email': user['email'],
                        'balance': float(user['balance']),
                        'id': user['id'],
                        'created_at': user['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                        'role': user['role'],
                    }
                    return f"SUCCESS|{json.dumps(user_data)}"
                else:
                    # Password does not match
                    return "FAILURE"
            else:
                # User not found
                return "NOT_FOUND"
        
        except Exception as e:
            # Log the error and return a friendly error message
            print("❌ login error:", e)
            return "ERROR|Internal error"

        finally:
            # Ensure that the cursor and connection are closed properly
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
    # -----------------------------
    # Register new user
    # -----------------------------
    @staticmethod
    def register(username, email, password):
        """
        Register a new user with the system.

        Args:
            username (str): Desired username.
            email (str): User's email address.
            password (str): Raw password (will be hashed).

        Returns:
            str: "SUCCESS" if registration is successful,
                 "EXISTS" if username already exists,
                 or "ERROR|..." on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            account = get_by_field(cursor, "users", "username", username, "one")

            if account:
                return "EXISTS"
            else:
                # Hash password and insert user with initial balance
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                data = {
                    'username': username,
                    'email': email,
                    'password_hash': password_hash,
                    'balance': 0.00,
                    'created_at': datetime.now()
                }
                add_into_table(cursor, "users", data)
                conn.commit()
                return "SUCCESS"
            
        except Exception as e:
        # Log the error and return a friendly error message
            print("❌ login error:", e)
            return "ERROR|Internal error"

        finally:
            # Ensure that the cursor and connection are closed properly
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # -----------------------------
    # Get profile by ID
    # -----------------------------
    @staticmethod
    def get_user_profile(id):
        """
        Retrieve user profile and booking statistics.

        Args:
            id (int): The user's ID.

        Returns:
            str: JSON string with user profile data and booking counts,
                 or error messages on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            user = get_by_field(cursor, "users", "id", id, "one")

            if user:
                # Convert balance from Decimal to float if necessary
                if isinstance(user['balance'], Decimal):
                    user['balance'] = float(user['balance'])
                
                # Check if 'created_at' is a string and convert to datetime
                if isinstance(user['created_at'], str):
                    user['created_at'] = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
                
                # Now format 'created_at' into the required string format
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')

                # Initialize counts for different booking statuses
                in_use_count = returned_count = canceled_count = waiting_count = 0

                # Count all statuses in a single query
                cursor.execute("""
                    SELECT status, COUNT(*) as count
                    FROM bookings
                    WHERE user_id = %s
                    GROUP BY status
                """, (id,))

                status_counts = cursor.fetchall()
                for row in status_counts:
                    status = row['status']
                    count = row['count']
                    if status == 'in-use':
                        in_use_count = count
                    elif status == 'returned':
                        returned_count = count
                    elif status == 'canceled':
                        canceled_count = count
                    elif status == 'waiting':
                        waiting_count = count

                # Build response with all the necessary user data and counts
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'balance': float(user['balance']),
                    'created_at': user['created_at'],
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'phone_number': user.get('phone_number'),
                    'in_use_count': in_use_count,
                    'returned_count': returned_count,
                    'canceled_count': canceled_count,
                    'waiting_count': waiting_count
                }

                return f"SUCCESS|{json.dumps(user_data)}"
            else:
                return "NOT_FOUND|User not found"

        except Exception as e:
            print("❌ get_user_profile error:", e)
            return "ERROR|Could not retrieve user profile"
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # -----------------------------
    # Update one field of a us
    # -----------------------------
    # Update one field of a user by ID
    # -----------------------------
    @staticmethod
    def update_field_by_id(id, field, value):
        """
        Retrieve user profile and booking statistics.

        Args:
            id (int): The user's ID.

        Returns:
            str: JSON string with user profile data and booking counts,
                 or error messages on failure.
        """
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"UPDATE users SET {field} = %s WHERE id = %s", (value, id))
        conn.commit()
        cursor.close()
        return cursor.rowcount > 0

    # -----------------------------
    # Get full user info + booking stats
    # -----------------------------
    @staticmethod
    def get_by_id(user_id):
        """
        Get detailed user info and booking counts by user ID.

        Args:
            user_id (int): ID of the user.

        Returns:
            str: JSON response with user details and booking stats,
                 or error message.
        """
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        try:
            # Get base user record
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                return "ERROR|User not found"

            # Initialize all counts to 0
            in_use_count = returned_count = canceled_count = waiting_count = 0

            # Count all statuses in a single query
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM bookings
                WHERE user_id = %s
                GROUP BY status
            """, (user_id,))

            status_counts = cursor.fetchall()
            for row in status_counts:
                status = row['status']
                count = row['count']
                if status == 'in_use':
                    in_use_count = count
                elif status == 'returned':
                    returned_count = count
                elif status == 'canceled':
                    canceled_count = count
                elif status == 'waiting':
                    waiting_count = count

            # Build response
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'balance': float(user['balance']),
                'created_at': user['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                'first_name': user.get('first_name'),
                'last_name': user.get('last_name'),
                'phone_number': user.get('phone_number'),
                'in_use_count': in_use_count,
                'returned_count': returned_count,
                'canceled_count': canceled_count,
                'waiting_count': waiting_count
            }

            return f"SUCCESS|{json.dumps(user_data)}"

        except Exception as e:
            print("❌ get_by_id error:", e)
            cursor.close()
            return "ERROR|Internal error"


    # -----------------------------
    # Update user's profile info (bulk)
    # -----------------------------
    @staticmethod
    def update_info(user_id, data_json):
        """
        Update multiple fields in a user’s profile using JSON input.

        Args:
            user_id (int): The user's ID.
            data_json (str): JSON string with updated fields.

        Returns:
            str: "SUCCESS|..." on success, or "ERROR|..." on failure.
        """
        try:
            data = json.loads(data_json)
            conn = get_db()
            cursor = conn.cursor()

            update_field(cursor, "users", data, user_id)

            conn.commit()
            return "SUCCESS|User info updated"
        except Exception as e:
            print("❌ update_info error:", e)
            return "ERROR|Could not update user info"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    # -----------------------------
    # Change user password (hashed)
    # -----------------------------
    @staticmethod
    def change_password(user_id, new_hashed_password):
        """
        Change the password of a user.

        Args:
            user_id (int): The user's ID.
            new_hashed_password (str): New password (hashed).

        Returns:
            str: "SUCCESS|..." on success, or "ERROR|..." on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()
            update_field(cursor, "users", {"password_hash": new_hashed_password}, user_id)
            conn.commit()
            return "SUCCESS|Password updated"
        except Exception as e:
            print("❌ change_password error:", e)
            return "ERROR|Failed to update password"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # -----------------------------
    # Add funds to user account
    # -----------------------------
    @staticmethod
    def top_up(user_id, amount):
        """
        Add balance to the user’s account and log the top-up history.

        Args:
            user_id (int): The user's ID.
            amount (float): Amount to top up.

        Returns:
            str: Success or failure message.
        """
        conn = None
        cursor = None
        try:
            if amount <= 0:
                return "FAILURE|Invalid top-up amount"

            conn = get_db()
            cursor = conn.cursor()

            # Step 1: Update user balance
            cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, user_id))

            # Step 2: Log top-up in history
            cursor.execute("INSERT INTO topups (user_id, amount) VALUES (%s, %s)", (user_id, amount))

            conn.commit()

            if cursor.rowcount > 0:
                return "SUCCESS|Top-up completed"
            else:
                return "FAILURE|User not found"

        except Exception as e:
            print(f"❌ Top-up failed: {e}")
            return "FAILURE|Top-up failed"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    # -----------------------------
    # Get user's booking history
    # -----------------------------
    @staticmethod
    def get_booking_history(user_id):
        """
        Fetch booking history for a user.

        Args:
            user_id (int): The user’s ID.

        Returns:
            str: JSON-formatted history of bookings.
        """
        try:
            print(f"📦 HISTORY requested for user_id: {user_id}")
            conn = get_db()
            if conn is None:
                return "FAILURE|[]"
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT
                    b.id AS id,
                    s.make,
                    s.color,
                    z.name AS location,
                    s.cost_per_minute,
                    b.rent_date,
                    b.checkin_time,
                    b.checkout_date,
                    b.status,
                    b.scooter_id,
                    b.total_price AS cost
                FROM bookings b
                JOIN scooters s ON b.scooter_id = s.id
                JOIN zones z ON s.zone_id = z.id
                WHERE b.user_id = %s
            """, (user_id,))

            results = cursor.fetchall()

            for row in results:
                row['cost'] = float(row['cost'])
                row['cost_per_minute'] = float(row['cost_per_minute'])

                for field in ['rent_date', 'checkin_time', 'checkout_time']:
                    if row.get(field):
                        row[field] = row[field].strftime('%Y-%m-%d %H:%M:%S')

            return f"SUCCESS|{json.dumps(results, default=str)}"

        except Exception as e:
            print("❌ get_booking_history error:", e)
            return "FAILURE|[]"
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

        
    @staticmethod
    def if_exist(username, email):
        """
        Check if a user already exists based on username or email.

        Args:
            username (str): Username to check.
            email (str): Email to check.

        Returns:
            str: "EXISTS" if found, otherwise "SUCCESS".
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Debugging: Print the values of username and email to ensure they are being passed correctly
            print(f"Checking if user exists with username: {username} or email: {email}")

            # Check if user already exists by username or email
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
            user = cursor.fetchone()

            if user:
                # If user is found, print the user info for debugging
                print(f"User found: {user}")
                cursor.close()
                return "EXISTS"  # User exists

            # If no user is found, return SUCCESS
            cursor.close()
            print("No user found. Registration can proceed.")
            return "SUCCESS"

        except Exception as e:
            print(f"❌ Error while checking if user exists: {e}")
            return f"ERROR|{str(e)}"  # Return the error message for 
        
    @staticmethod
    def get_user_id_by_email(email):
        """
        Retrieve a user’s ID by their email.

        Args:
            email (str): The user's email address.

        Returns:
            str: "SUCCESS|<user_id>" or "ERROR|..." on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user:
                return f"SUCCESS|{user['id']}"
            else:
                return "ERROR|User not found"

        except Exception as e:
            print(f"❌ get_user_id_by_email error: {e}")
            return f"ERROR|{str(e)}"
        
    ALLOWED_ROLES = ('customer', 'engineer')

    @staticmethod
    def get_all_users(role: str):
        """
        Retrieve users of a given role, or ALL to fetch both.
        """
        # Accept “ALL” to mean both roles
        if role.lower() == 'all':
            roles = User.ALLOWED_ROLES
        elif role.lower() in User.ALLOWED_ROLES:
            roles = [role.lower()]
        else:
            return "ERROR|Invalid role"

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"""
                SELECT id, username, first_name, last_name,
                    email, phone_number, balance, role, created_at
                FROM users
                WHERE role IN ({', '.join(['%s']*len(roles))})
                ORDER BY username
            """, tuple(roles))
            users = cursor.fetchall()
            if not users:
                return "NOT_FOUND"
            for u in users:
                if isinstance(u.get('balance'), Decimal):
                    u['balance'] = float(u['balance'])
                if isinstance(u.get('created_at'), datetime):
                    u['created_at'] = u['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            return f"SUCCESS|{json.dumps(users)}"
        except Exception as e:
            print("❌ get_all_users error:", e)
            return f"ERROR|{e}"
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_user_details(user_id: int):
        """
        Get details for a single user (customer or engineer).
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or user.get('role') not in User.ALLOWED_ROLES:
                return "FAILURE|User not found"
            # normalize fields
            if isinstance(user.get('balance'), Decimal):
                user['balance'] = float(user['balance'])
            if isinstance(user.get('created_at'), datetime):
                user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            # remove password_hash for safety
            user.pop('password_hash', None)
            return f"SUCCESS|{json.dumps(user)}"

        except Exception as e:
            print("❌ get_user_details error:", e)
            return f"ERROR|{e}"
        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def add_user(role: str, username: str, email: str, password: str,
                 first_name: str = None, last_name: str = None, phone_number: str = None):
        """
        Insert a new user with given role.
        """
        if role not in User.ALLOWED_ROLES:
            return "ERROR|Invalid role"
        try:
            # check exists
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                           (username, email))
            if cursor.fetchone():
                return "EXISTS"

            # hash and insert
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            now = datetime.now()
            cursor.execute("""
                INSERT INTO users
                    (username, email, password_hash,
                     first_name, last_name, phone_number,
                     balance, role, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                username, email, password_hash,
                first_name or '', last_name or '', phone_number or '',
                0.00, role, now
            ))
            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("❌ add_user error:", e)
            return f"ERROR|{e}"
        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def edit_user(user_id: int, data_json: str):
        """
        Update multiple fields (first_name, last_name, phone_number, balance, etc.).
        """
        try:
            data = json.loads(data_json)
            # optionally: validate no forbidden keys
            conn = get_db()
            cursor = conn.cursor()
            # build SET clause dynamically
            fields = []
            values = []
            for k, v in data.items():
                fields.append(f"{k} = %s")
                values.append(v)
            values.append(user_id)

            sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s AND role IN (%s, %s)"
            cursor.execute(sql, values + list(User.ALLOWED_ROLES))
            conn.commit()
            return "SUCCESS" if cursor.rowcount else "FAILURE|User not found"

        except Exception as e:
            print("❌ edit_user error:", e)
            return f"ERROR|{e}"
        finally:
            cursor.close()
            conn.close()


    @staticmethod
    def delete_user(user_id: int):
        """
        Delete a user (customer or engineer) and all their bookings.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # 1) Remove all of this user's bookings
            cursor.execute("DELETE FROM bookings WHERE user_id = %s", (user_id,))

            # 2) Then delete the user
            cursor.execute(
                "DELETE FROM users WHERE id = %s AND role IN (%s, %s)",
                (user_id, *User.ALLOWED_ROLES)
            )

            conn.commit()
            return "SUCCESS" if cursor.rowcount else "FAILURE|User not found"
        except Exception as e:
            print("❌ delete_user error:", e)
            return f"ERROR|{e}"
        finally:
            cursor.close()
            conn.close()
    
 


    @staticmethod
    def get_all_topups():
        """
        Return all top-up records with user information.

        Returns:
            str: SUCCESS|[...] or ERROR|<message>
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    t.id, 
                    t.user_id, 
                    u.username, 
                    t.amount, 
                    t.topped_up_at AS timestamp
                FROM topups t
                LEFT JOIN users u ON t.user_id = u.id
                ORDER BY t.topped_up_at DESC
            """)

            rows = cursor.fetchall()

            for row in rows:
                if isinstance(row["timestamp"], datetime):
                    row["timestamp"] = row["timestamp"].strftime('%Y-%m-%d %H:%M:%S')


            return f"SUCCESS|{json.dumps(rows, default=decimal_default)}"

        except Exception as e:
            print("❌ get_all_topups error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def checking_qr(scooter_id):
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            scooter = get_by_field(cursor, "scooters", "id", scooter_id, "one")


            if scooter["status"] == "booked":
                return f"SUCCESS|WILL_CHECKIN"
            elif scooter["status"] == "in_use":
                return f"SUCCESS|WILL_CHECKOUT"
            else:
                return f"SUCCESS|NOT_BOOK"
        except Exception as e:
            print("❌ checking_qr error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def qr_proccess(scooter_id, username, action):
        from .BookingService import Booking

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            

            scooter = get_by_field(cursor, "scooters", "id", scooter_id, "one")
            user= get_by_field(cursor, "users", "username", username, "one")

            if user is None:
                return "NO_USER_FOUND"

            if action == "NOT_BOOK" :
                return "NOT_BOOKED"
            
            cursor.execute("""
                SELECT *
                FROM bookings b
                WHERE user_id = %s AND scooter_id = %s AND status != 'return' AND status != 'canceled'
            """, (user['id'], scooter_id))

            booking = cursor.fetchone()

            if action == "WILL_CHECKIN":
                checking_time = get_time()
                response = Booking.checkin_booking(booking["id"], checking_time)
                if response == "SUCCESS":
                    return "SUCCESS_CHECK_IN"

            elif action == "WILL_CHECKOUT":
                checkout_time = get_time()
                times = calculate_total_time(str(booking['checkin_time']), checkout_time)
                price = times * scooter["cost_per_minute"]
                response = Booking.checkout_booking(booking["id"], checkout_time, price)
                if response == "SUCCESS":
                    return "SUCCESS_CHECK_OUT"
                elif response == "INSUFFICIENT_BALANCE":
                    return "INSUFFICIENT_BALANCE"

        except Exception as e:
            print("❌ qr_process error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def create_comment(username, scooter_id, comment):
        """
        Create a comment for a scooter.

        Args:
            user_id (int): The user's ID.
            scooter_id (int): The scooter's ID.
            comment (str): The comment text.

        Returns:
            str: "SUCCESS" or "ERROR|..." on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Insert the comment into the database
            cursor.execute("""
                INSERT INTO comments (username, scooter_id, context)
                VALUES (%s, %s, %s)
            """, (username, scooter_id, comment))

            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("❌ create_comment error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")
