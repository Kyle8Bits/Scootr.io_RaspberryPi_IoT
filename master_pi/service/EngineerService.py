from datetime import datetime
from ..database.db_connect import db_connect as get_db
from .crud import get_by_field, update_field, add_into_table, get_all_from_table
import json

class Engineer:
    @staticmethod
    def engineer_claim_issue(issue_id, engineer_id):
        """
        Assigns an engineer to a specific approved issue.

        Args:
            issue_id (int): The ID of the issue to claim.
            engineer_id (int): The ID of the engineer claiming the issue.

        Returns:
            str: Result message indicating success or failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Update the engineer_id for the given issue_id
            cursor.execute("""
                UPDATE approved_issues
                SET engineer_id = %s
                WHERE issue_id = %s
            """, (engineer_id, issue_id))
            conn.commit()

            return "SUCCESS|Engineer assigned to issue"
        except Exception as e:
            print("❌ engineer_claim_issue error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def get_all_approve_issues_details():
        """
        Retrieves all approved issue details where engineer has not claimed the issue yet.

        Returns:
            str: "SUCCESS|<json_payload>" or "FAILURE|<error>"
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            # Step 1: Get all unclaimed approved issue_ids
            cursor.execute("""
                SELECT issue_id
                FROM approved_issues
                WHERE engineer_id IS NULL
                ORDER BY approved_at DESC
            """)
            issue_ids = [row["issue_id"] for row in cursor.fetchall()]

            if not issue_ids:
                return "SUCCESS|[]"

            # Step 2: Fetch full issue details for those IDs
            query = f"""
                SELECT 
                    id,
                    scooter_id,
                    customer_id,
                    issue_type,
                    additional_details,
                    latitude,
                    longitude,
                    reported_at,
                    status,
                    updated_at
                FROM issues
                WHERE id IN ({','.join(['%s'] * len(issue_ids))})
                ORDER BY reported_at DESC
            """
            cursor.execute(query, tuple(issue_ids))
            issues = cursor.fetchall()

            return "SUCCESS|" + json.dumps(issues, default=str)

        except Exception as e:
            print("❌ get_all_approve_issues_details error:", e)
            return f"FAILURE|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def get_issues_assigned_to_engineer(engineer_id):
        """
        Returns all issues approved and assigned to a specific engineer.

        Args:
            engineer_id (int): The ID of the engineer.

        Returns:
            str: "SUCCESS|<json>" or "FAILURE|<error>"
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
                    i.reported_at,
                    i.status,
                    i.updated_at,
                    i.latitude,
                    i.longitude,
                    ai.approved_at,
                    ai.resolved_at
                FROM issues i
                JOIN approved_issues ai ON i.id = ai.issue_id
                WHERE ai.engineer_id = %s
                ORDER BY ai.approved_at DESC
            """, (engineer_id,))

            issues = cursor.fetchall()
            return f"SUCCESS|{json.dumps(issues, default=str)}"

        except Exception as e:
            print("❌ get_issues_assigned_to_engineer error:", e)
            return f"FAILURE|{str(e)}"

        finally:
            if cursor: cursor.close()
            if conn: conn.close()


    @staticmethod
    def mark_resolved(issue_id, engineer_id, resolution_type, resolution_details):
        """
        Mark issue as resolved and set scooter as available.
        """
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Step 1: Update issue status
            cursor.execute("""
                UPDATE issues
                SET status = 'Resolved', updated_at = NOW()
                WHERE id = %s
            """, (issue_id,))

            # Step 2: Update approved_issues resolution info
            cursor.execute("""
                UPDATE approved_issues
                SET resolved_at = NOW(),
                    resolution_type = %s,
                    resolution_details = %s
                WHERE issue_id = %s AND engineer_id = %s
            """, (resolution_type, resolution_details, issue_id, engineer_id))

            # Step 3: Find scooter_id from issue
            cursor.execute("SELECT scooter_id FROM issues WHERE id = %s", (issue_id,))
            scooter_row = cursor.fetchone()

            if scooter_row:
                scooter_id = scooter_row[0]

                # Step 4: Update scooter status to available
                cursor.execute("""
                    UPDATE scooters
                    SET status = 'available'
                    WHERE id = %s
                """, (scooter_id,))

            conn.commit()
            return "SUCCESS"

        except Exception as e:
            print("❌ mark_resolved error:", e)
            return f"FAILURE|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()


    @staticmethod
    def get_resolved_issues(engineer_id):
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT 
                    ai.issue_id,
                    i.scooter_id,
                    i.issue_type,
                    ai.approved_at,  
                    ai.resolved_at,
                    ai.resolution_type,
                    ai.resolution_details
                FROM approved_issues ai
                JOIN issues i ON ai.issue_id = i.id
                WHERE ai.engineer_id = %s AND ai.resolved_at IS NOT NULL
                ORDER BY ai.resolved_at DESC
            """, (engineer_id,))

            data = cursor.fetchall()
            return "SUCCESS|" + json.dumps(data, default=str)

        except Exception as e:
            print("❌ get_resolved_issues error:", e)
            return f"FAILURE|{str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    @staticmethod
    def handle_engineer_scan(engineer_id, scooter_id):
        """
        Handle the engineer's scan of a scooter.

        Args:
            engineer_id (int): The engineer's ID.
            scooter_id (int): The scooter's ID.

        Returns:
            str: "SUCCESS" or "ERROR|..." on failure.
        """
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            user = get_by_field(cursor,"users", "id", engineer_id, "one")

            if not user:
                return "ERROR|Engineer not found"


            scooter = get_by_field(cursor,"scooters", "id", scooter_id, "one")

            if scooter['status'] not in ['to_be_repaired', 'under_repair']:
                return "ERROR|Scooter is not in a repairable state"

            issue = cursor.execute("""
                SELECT *
                FROM issues
                WHERE scooter_id = %s AND status = 'Approved'
            """, (scooter_id,))

            issue = cursor.fetchone()

            if not issue:
                return "ERROR|Admin has not approved the issue yet"
            
            approved_issue = get_by_field(cursor, "approved_issues", "issue_id", issue['id'], "one")

            if scooter['status'] == 'to_be_repaired':
                update_field(cursor ,"approved_issues", {'engineer_id': engineer_id}, approved_issue['id'])
                update_field(cursor, "scooters", {'status': 'under_repair'}, scooter_id)
                conn.commit()
                return "SUCCESS|Scooter is now lock for repairing"
            
            elif scooter['status'] == 'under_repair':
                update_field(cursor, "scooters", {'status': 'available'}, scooter_id)
                conn.commit()
                return "SUCCESS|Scooter is now available"


        except Exception as e:
            print("❌ handle_engineer_scan error:", e)
            return f"ERROR|{str(e)}"

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
