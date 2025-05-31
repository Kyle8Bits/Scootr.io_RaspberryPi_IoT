from datetime import datetime
from ..database.db_connect import db_connect as get_db
import json
from .crud import get_by_field, update_field, add_into_table, get_all_from_table


class Admin:
    
    @staticmethod
    def get_all_engineers_email():
        """
        Retrieves a list of all engineer emails.

        Returns:
            str: "SUCCESS|<json_array_of_emails>" or "ERROR|<message>"
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT email
                FROM users
                WHERE role = %s
                ORDER BY id
            """, ("engineer",))
            users = cursor.fetchall()
            if not users:
                return "NOT_FOUND"

            emails = [u["email"] for u in users if u.get("email")]
            return f"SUCCESS|{json.dumps(emails)}"
        except Exception as e:
            print("❌ get_all_engineers_email error:", e)
            return f"ERROR|{str(e)}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                
    @staticmethod
    def approve_issue(issue_id):
        """
        Approve an issue report.

        Args:
            issue_id (int): The ID of the issue to approve.

        Returns:
            str: Result message indicating success or failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Step 1: Update the issue status in the main table
            cursor.execute("""
                UPDATE issues
                SET status = 'Approved', updated_at = NOW()
                WHERE id = %s AND status = 'Open'
            """, (issue_id,))

            # issuse = get_by_field("issues", "id", issue_id)
            
            if cursor.rowcount == 0:
                return "FAILURE|Issue not found or not open"

            # Step 2: Log to approved_issues table (optional audit trail)
            cursor.execute("""
                INSERT INTO approved_issues (issue_id, approved_at)
                VALUES (%s, %s)
            """, (issue_id, datetime.now()))
            
            conn.commit()
            return "SUCCESS|Issue approved"
        
        except Exception as e:
            print("❌ approve_issue error:", e)
            return f"FAILURE|{str(e)}"
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
