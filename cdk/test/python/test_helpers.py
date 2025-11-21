"""Tests for helper functions"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import handler


class TestParseTime:
    """Tests for parse_time function"""

    def test_parse_time_9am(self):
        """Test parsing 9:00 AM"""
        result = handler.parse_time("9:00 AM")
        assert result == 540  # 9 * 60

    def test_parse_time_12pm(self):
        """Test parsing 12:00 PM (noon)"""
        result = handler.parse_time("12:00 PM")
        assert result == 720  # 12 * 60

    def test_parse_time_12am(self):
        """Test parsing 12:00 AM (midnight)"""
        result = handler.parse_time("12:00 AM")
        assert result == 0

    def test_parse_time_6_30pm(self):
        """Test parsing 6:30 PM"""
        result = handler.parse_time("6:30 PM")
        assert result == 1110  # (6 + 12) * 60 + 30

    def test_parse_time_with_whitespace(self):
        """Test parsing time with extra whitespace"""
        result = handler.parse_time("  9:00 AM  ")
        assert result == 540

    def test_parse_time_lowercase(self):
        """Test parsing time with lowercase am/pm"""
        result = handler.parse_time("9:00 am")
        assert result == 540

    def test_parse_time_without_minutes(self):
        """Test parsing time without minutes specified"""
        result = handler.parse_time("9 AM")
        assert result == 540

    def test_parse_time_invalid_format(self):
        """Test parsing invalid time format"""
        result = handler.parse_time("invalid")
        assert result == 0

    def test_parse_time_empty_string(self):
        """Test parsing empty string"""
        result = handler.parse_time("")
        assert result == 0


class TestParseSessionDatetime:
    """Tests for parse_session_datetime function"""

    def test_parse_valid_datetime(self):
        """Test parsing valid date and time"""
        result = handler.parse_session_datetime("Nov 25, 2025", "9:00 AM")

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 25
        assert result.hour == 9
        assert result.minute == 0
        assert result.tzinfo == ZoneInfo("Europe/Paris")

    def test_parse_afternoon_time(self):
        """Test parsing afternoon time"""
        result = handler.parse_session_datetime("Nov 26, 2025", "2:30 PM")

        assert result is not None
        assert result.hour == 14
        assert result.minute == 30

    def test_parse_midnight(self):
        """Test parsing midnight (12:00 AM)"""
        result = handler.parse_session_datetime("Nov 25, 2025", "12:00 AM")

        assert result is not None
        assert result.hour == 0
        assert result.minute == 0

    def test_parse_noon(self):
        """Test parsing noon (12:00 PM)"""
        result = handler.parse_session_datetime("Nov 25, 2025", "12:00 PM")

        assert result is not None
        assert result.hour == 12
        assert result.minute == 0

    def test_parse_invalid_date(self):
        """Test parsing invalid date"""
        result = handler.parse_session_datetime("Invalid Date", "9:00 AM")
        assert result is None

    def test_parse_invalid_time(self):
        """Test parsing invalid time"""
        result = handler.parse_session_datetime("Nov 25, 2025", "invalid")
        assert result is None

    def test_parse_empty_strings(self):
        """Test parsing empty strings"""
        result = handler.parse_session_datetime("", "")
        assert result is None


class TestGetParisNow:
    """Tests for get_paris_now function"""

    def test_returns_datetime_with_paris_timezone(self):
        """Test that get_paris_now returns datetime in Paris timezone"""
        result = handler.get_paris_now()

        assert isinstance(result, datetime)
        assert result.tzinfo == ZoneInfo("Europe/Paris")

    def test_returns_current_time(self):
        """Test that get_paris_now returns current time (approximately)"""
        before = datetime.now(ZoneInfo("Europe/Paris"))
        result = handler.get_paris_now()
        after = datetime.now(ZoneInfo("Europe/Paris"))

        # Result should be between before and after (within a few seconds)
        assert before <= result <= after


class TestFilterSessionsByNow:
    """Tests for filter_sessions_by_now function"""

    def test_ongoing_session_detection(self):
        """Test detection of ongoing sessions"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:30 AM",
            "endTime": "10:00 AM",
            "_start_dt": datetime(2025, 11, 25, 9, 30, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 10, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to 9:45 AM (during session)
        mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        assert len(result["ongoing"]) == 1
        assert result["ongoing"][0]["id"] == "session-1"
        assert len(result["upcoming"]) == 0

    def test_upcoming_session_detection(self):
        """Test detection of upcoming sessions (within 30 min)"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "10:00 AM",
            "endTime": "10:30 AM",
            "_start_dt": datetime(2025, 11, 25, 10, 0, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 10, 30, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to 9:45 AM (15 min before session)
        mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        assert len(result["ongoing"]) == 0
        assert len(result["upcoming"]) == 1
        assert result["upcoming"][0]["id"] == "session-1"

    def test_session_starting_exactly_now(self):
        """Test session starting exactly at current time"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:45 AM",
            "endTime": "10:15 AM",
            "_start_dt": datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 10, 15, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to exactly start time
        mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        # Session starting now should be in ongoing
        assert len(result["ongoing"]) == 1

    def test_session_ending_exactly_now(self):
        """Test session ending exactly at current time"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:00 AM",
            "endTime": "10:00 AM",
            "_start_dt": datetime(2025, 11, 25, 9, 0, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 10, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to exactly end time
        mock_time = datetime(2025, 11, 25, 10, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        # Session ending now should still be in ongoing
        assert len(result["ongoing"]) == 1

    def test_past_session_excluded(self):
        """Test that past sessions are excluded"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:00 AM",
            "endTime": "9:30 AM",
            "_start_dt": datetime(2025, 11, 25, 9, 0, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 9, 30, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to 10:00 AM (past session)
        mock_time = datetime(2025, 11, 25, 10, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        assert len(result["ongoing"]) == 0
        assert len(result["upcoming"]) == 0

    def test_future_session_outside_window_excluded(self):
        """Test that sessions starting >30 min in future are excluded"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "11:00 AM",
            "endTime": "11:30 AM",
            "_start_dt": datetime(2025, 11, 25, 11, 0, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": datetime(2025, 11, 25, 11, 30, 0, tzinfo=ZoneInfo("Europe/Paris"))
        }]

        # Mock current time to 9:00 AM (2 hours before)
        mock_time = datetime(2025, 11, 25, 9, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        assert len(result["ongoing"]) == 0
        assert len(result["upcoming"]) == 0

    def test_session_without_parsed_datetime_skipped(self):
        """Test that sessions without _start_dt are skipped"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:30 AM",
            "endTime": "10:00 AM",
            # Missing _start_dt and _end_dt
        }]

        mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        # Should not crash, just skip the session
        assert len(result["ongoing"]) == 0
        assert len(result["upcoming"]) == 0

    def test_session_with_invalid_end_time_uses_fallback(self):
        """Test fallback duration when end time is invalid"""
        sessions = [{
            "id": "session-1",
            "date": "Nov 25, 2025",
            "startTime": "9:30 AM",
            "endTime": "invalid",
            "_start_dt": datetime(2025, 11, 25, 9, 30, 0, tzinfo=ZoneInfo("Europe/Paris")),
            "_end_dt": None  # Invalid end time
        }]

        # Mock current time to 9:35 AM (5 min after start)
        mock_time = datetime(2025, 11, 25, 9, 35, 0, tzinfo=ZoneInfo("Europe/Paris"))

        with patch('handler.get_paris_now', return_value=mock_time):
            result = handler.filter_sessions_by_now(sessions)

        # Should assume 20 min duration, so still ongoing at 9:35
        assert len(result["ongoing"]) == 1
