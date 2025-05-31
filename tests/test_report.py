import sys
import re
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master_pi')))

from unittest.mock import patch, MagicMock
from master_pi.service.ReportService import Report

def test_successful_issue_report():
    # Mock data
    mock_customer_id = 1
    mock_scooter_id = 2
    mock_issue_type = "Broken Wheel"
    mock_additional_details = "Front wheel is damaged"

    with patch('master_pi.service.ReportService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = Report.report_issue(
            mock_customer_id,
            mock_scooter_id,
            mock_issue_type,
            mock_additional_details,
            latitude=0.0,
            longitude=0.0
        )
        assert result.startswith("SUCCESS")


def test_issue_report_with_exception():
    # Mock data
    mock_customer_id = 1
    mock_scooter_id = 2
    mock_issue_type = "Broken Wheel"
    mock_additional_details = "Front wheel is damaged"
    mock_error_message = "Database connection failed"

    with patch('master_pi.service.ReportService.get_db') as mock_get_db:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception(mock_error_message)

        result = Report.report_issue(
            mock_customer_id,
            mock_scooter_id,
            mock_issue_type,
            mock_additional_details,
            latitude=0.0,
            longitude=0.0
        )
        assert result.startswith("FAILURE|")
