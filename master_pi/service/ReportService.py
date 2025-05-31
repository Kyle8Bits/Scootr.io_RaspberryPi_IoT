from datetime import datetime
from ..database.db_connect import db_connect as get_db
import json
class Report:
    """
    Handles issue reporting related to scooters.
    """

    @staticmethod
    def report_issue(customer_id, scooter_id, issue_type, additional_details, latitude, longitude):
        """
        Submits a new issue report and updates the scooter status to 'To Be Repaired'.

        Args:
            customer_id (int): The ID of the customer reporting the issue.
            scooter_id (int): The ID of the affected scooter.
            issue_type (str): Type of issue (e.g., battery, brake).
            additional_details (str): Additional details provided by the customer.

        Returns:
            str: Result message indicating success or failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Insert a new issue record into the database
            cursor.execute("""
                INSERT INTO issues (customer_id, scooter_id, issue_type, additional_details, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer_id, scooter_id, issue_type, additional_details, latitude, longitude))
            conn.commit()
           
            # Update the scooter's status to 'To Be Repaired'
            cursor.execute("""
                UPDATE scooters
                SET status = 'to_be_repaired'
                WHERE id = %s
            """, (scooter_id,))
            conn.commit()

            return "SUCCESS|Issue reported"
        except Exception as e:
            print("❌ report_issue error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()



    @staticmethod
    def get_all_issues():
        """
        Retrieves all scooter issue reports for admin review.

        Returns:
            str: "SUCCESS|<json_payload>" or "FAILURE|<error>"
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    i.id,
                    i.scooter_id,
                    i.customer_id,
                    i.issue_type,
                    i.additional_details,
                    i.latitude,
                    i.longitude,
                    i.reported_at,
                    i.status,
                    i.updated_at
                FROM issues i
                ORDER BY i.reported_at DESC
            """)
            issues = cursor.fetchall()
            return "SUCCESS|" + json.dumps(issues, default=str)

        except Exception as e:
            print("❌ get_all_issues error:", e)
            return f"FAILURE|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @staticmethod
    def get_issue_by_id(issue_id):
        """
        Retrieve a single scooter issue report by ID.

        Args:
            issue_id (int): The ID of the issue to retrieve.

        Returns:
            str: "SUCCESS|<json_payload>" or "FAILURE|<error>"
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM issues WHERE id = %s", (issue_id,))
            issue = cursor.fetchone()

            if not issue:
                return "FAILURE|Issue not found"

            return "SUCCESS|" + json.dumps(issue, default=str)

        except Exception as e:
            print("❌ get_issue_by_id error:", e)
            return f"FAILURE|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def mark_as_resolved(issue_id):
        """
        Marks an issue as resolved by updating its status and timestamp.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE issues
                SET status = 'Resolved',
                    updated_at = NOW()
                WHERE id = %s
            """, (issue_id,))
            conn.commit()

            return "SUCCESS|Issue resolved"
        except Exception as e:
            print("❌ mark_as_resolved error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    @staticmethod
    def get_report_count(user_id):
        """
        Returns the total number of issue reports submitted by a specific user.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM issues WHERE customer_id = %s
            """, (user_id,))
            result = cursor.fetchone()

            count = result[0] if result else 0
            return f"SUCCESS|{count}"
        except Exception as e:
            print("❌ get_report_count error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
