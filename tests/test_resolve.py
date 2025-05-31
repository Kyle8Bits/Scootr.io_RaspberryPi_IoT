import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Adjust path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))

from master_pi.service.ReportService import Report  # Assuming your class is named `Issue` and method is under IssueService

def test_mark_as_resolved_success():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    with patch('master_pi.service.ReportService.get_db', return_value=mock_conn):
        mock_conn.cursor.return_value = mock_cursor

        result = Report.mark_as_resolved(123)

        mock_cursor.execute.assert_called_once_with(
            """
                UPDATE issues
                SET status = 'Resolved',
                    updated_at = NOW()
                WHERE id = %s
            """, (123,)
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert result == "SUCCESS|Issue resolved"

def test_mark_as_resolved_failure():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    with patch('master_pi.service.ReportService.get_db', return_value=mock_conn):
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("DB Failure")

        result = Report.mark_as_resolved(999)

        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

        assert result.startswith("FAILURE|")
        assert "DB Failure" in result

