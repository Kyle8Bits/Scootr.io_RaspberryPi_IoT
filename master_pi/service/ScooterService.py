from ..database.db_connect import db_connect as get_db
import json
from decimal import Decimal
from .crud import get_by_field, update_field, add_into_table, get_all_from_table

class Scooter:
    """
    A class for handling scooter-related operations in the system,
    including retrieval, status updates, and detail lookups.
    """

    @staticmethod
    def get_all_scooter():
        """
        Retrieve all scooters from the database, including zone (location) names.

        Returns:
            str: "SUCCESS|<json>" if scooters are found, "NOT_FOUND" if no scooters exist,
                or "ERROR|<message>" if an exception occurs.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    s.id,
                    s.make,
                    s.color,
                    z.name AS location,
                    s.power_remaining,
                    s.cost_per_minute,
                    s.status,
                    s.image_url
                FROM scooters s
                LEFT JOIN zones z ON s.zone_id = z.id
            """

            cursor.execute(query)
            scooters = cursor.fetchall()

            if not scooters:
                return "NOT_FOUND"

            for scooter in scooters:
                for key, value in scooter.items():
                    if isinstance(value, Decimal):
                        scooter[key] = float(value)

            return f"SUCCESS|{json.dumps(scooters)}"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def get_all_zones():
        """
        Retrieve all zones from the database.

        Returns:
            str: "SUCCESS|<json>" if zones are found,
                 "NOT_FOUND" if no zones exist,
                 or "ERROR|<message>" if an exception occurs.
        """
        conn = None
        cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id, name FROM zones ORDER BY name")
            zones = cursor.fetchall()

            if not zones:
                return "NOT_FOUND"

            # no Decimal fields here, but pattern maintained
            return f"SUCCESS|{json.dumps(zones)}"

        except Exception as e:
            print("ERROR in get_all_zones: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    

    @staticmethod
    def change_availability(id, status):
        """
        Change the availability status of a scooter.

        Args:
            id (int): The ID of the scooter.
            status (str): The new status to assign (e.g., 'available', 'booked', etc.).
        """
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE scooters
            SET status = %s 
            WHERE id = %s
        """, (status, id))

        cursor.execute("""
            UPDATE scooters
            SET status = %s 
            WHERE id = %s
        """, (status, id))

        conn.commit()
        cursor.close()

    @staticmethod
    def get_scooter_details(id):
        """
        Get the details of a specific scooter by ID.

        Args:
            id (int): The ID of the scooter to retrieve.

        Returns:
            str: "SUCCESS|<json>" with scooter details if found,
                 "FAILURE|Scooter not found" if not,
                 or "ERROR|<message>" if an exception occurs.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            scooter = get_by_field(cursor, "scooters", "id", id, "one")
            if scooter is None:
                return "FAILURE|Scooter not found"
            location = get_by_field(cursor, "zones", "id", scooter["zone_id"], "one")
            comments = get_by_field(cursor, "comments", "scooter_id", id, "all")

            if scooter is None:
                return "FAILURE|Scooter not found"
            else:
                if location:
                    scooter['location'] = location['name']
                # Convert any Decimal values to float
                for key, value in scooter.items():
                    if isinstance(value, Decimal):
                        scooter[key] = float(value)
                if comments:
                    for comment in comments:
                        for key, value in comment.items():
                            if isinstance(value, Decimal):
                                comment[key] = float(value)
                                
                    scooter['comments'] = comments
                else:
                    scooter['comments'] = []

                return f"SUCCESS|{json.dumps(scooter)}"

        except Exception as e:
            print("ERROR: " + str(e))
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
    @staticmethod
    def get_scooter_by_id(id):
        conn = None
        cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            # Safe cast to int
            id = int(id)

            scooter = get_by_field(cursor, "scooters", "id", id, "one")

            if scooter is None:
                return "FAILURE|Scooter not found"
            else:
                # Convert Decimal to float for JSON safety
                for key, value in scooter.items():
                    if isinstance(value, Decimal):
                        scooter[key] = float(value)

                return f"SUCCESS|{json.dumps(scooter)}"
        except Exception as e:
            print("❌ ERROR in get_scooter_by_id:", e)
            return f"ERROR|{str(e)}"
        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()

    @staticmethod
    def add_scooter(make, color, zone_id, battery, cost, status):
        """
        Insert a new scooter, linking to the zones table via zone_id.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO scooters 
                  (make, color, zone_id, power_remaining, cost_per_minute, status)
                VALUES (%s,      %s,    %s,       %s,               %s,            %s)
            """, (make, color, zone_id, battery, cost, status))

            conn.commit()
            return "SUCCESS"
        except Exception as e:
            return f"ERROR|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()



    @staticmethod
    def edit_scooter(scooter_id, make, color, zone_id, battery, cost, status):
        """
        Update an existing scooter’s details, including its zone_id.
        Returns:
            "SUCCESS" on success, or "ERROR|<message>" on failure.
        """
        conn = None
        cursor = None
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE scooters
                SET make            = %s,
                    color           = %s,
                    zone_id         = %s,
                    power_remaining = %s,
                    cost_per_minute = %s,
                    status          = %s
                WHERE id = %s
            """, (make, color, zone_id, battery, cost, status, scooter_id))

            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("ERROR in edit_scooter:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()



    @staticmethod
    def delete_scooter(scooter_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scooters WHERE id = %s", (scooter_id,))
            conn.commit()
            return "SUCCESS"
        except Exception as e:
            return f"ERROR|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    @staticmethod
    def update_scooter_power(scooter_id, power):
        """
        Update the battery level of a scooter.

        Args:
            scooter_id (int): The ID of the scooter.
            battery (float): The new battery level to set.

        Returns:
            str: "SUCCESS" if the update was successful,
                 or "ERROR|<message>" if an exception occurs.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            update_field(cursor, "scooters",{"power_remaining": power} , scooter_id)
            conn.commit()

            return "SUCCESS"
        except Exception as e:
            print("ERROR in update_scooter_battery:", e)
            return f"ERROR|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

