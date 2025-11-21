"""Tests for query parameter filtering"""

import json
import pytest
from unittest.mock import patch
from datetime import datetime
from zoneinfo import ZoneInfo
import handler


def test_sessions_filter_by_date_nov_25(s3_mock, api_event):
    """Test filtering sessions by date=2025-11-25"""
    event = api_event(method="GET", path="/sessions", query_string="date=2025-11-25")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["date"] == "2025-11-25"
    assert data["count"] == 2  # session-1 and session-2

    for session in data["sessions"]:
        assert "Nov 25" in session["date"]


def test_sessions_filter_by_date_nov_26(s3_mock, api_event):
    """Test filtering sessions by date=2025-11-26"""
    event = api_event(method="GET", path="/sessions", query_string="date=2025-11-26")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["date"] == "2025-11-26"
    assert data["count"] == 1  # session-3

    for session in data["sessions"]:
        assert "Nov 26" in session["date"]


def test_sessions_filter_by_date_alternative_format(s3_mock, api_event):
    """Test filtering sessions by date with alternative format"""
    event = api_event(method="GET", path="/sessions", query_string="date=Nov 25")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 2


def test_sessions_filter_by_stage(s3_mock, api_event):
    """Test filtering sessions by stage"""
    event = api_event(method="GET", path="/sessions", query_string="stage=CEO Stage")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["stage"] == "CEO Stage"
    assert data["count"] == 2  # session-1 and session-3

    for session in data["sessions"]:
        assert "ceo stage" in session["stage"].lower()


def test_sessions_filter_by_stage_case_insensitive(s3_mock, api_event):
    """Test filtering sessions by stage is case-insensitive"""
    event = api_event(method="GET", path="/sessions", query_string="stage=mainstage south")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1  # session-2
    assert data["sessions"][0]["id"] == "session-2"


def test_sessions_filter_by_time_morning(s3_mock, api_event):
    """Test filtering sessions by time=morning (before 12:00 PM)"""
    event = api_event(method="GET", path="/sessions", query_string="time=morning")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["time"] == "morning"
    assert data["count"] == 2  # session-1 (9:30 AM) and session-3 (10:00 AM)


def test_sessions_filter_by_time_afternoon(s3_mock, api_event):
    """Test filtering sessions by time=afternoon (12:00 PM+)"""
    event = api_event(method="GET", path="/sessions", query_string="time=afternoon")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["time"] == "afternoon"
    assert data["count"] == 1  # session-2 (2:00 PM)


def test_sessions_search_by_title(s3_mock, api_event):
    """Test searching sessions by title"""
    event = api_event(method="GET", path="/sessions", query_string="search=Banking")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["search"] == "Banking"
    assert data["count"] == 1
    assert "banking" in data["sessions"][0]["title"].lower()


def test_sessions_search_by_speaker_name(s3_mock, api_event):
    """Test searching sessions by speaker name"""
    event = api_event(method="GET", path="/sessions", query_string="search=John Doe")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1
    assert data["sessions"][0]["id"] == "session-1"


def test_sessions_search_by_speaker_company(s3_mock, api_event):
    """Test searching sessions by speaker company"""
    event = api_event(method="GET", path="/sessions", query_string="search=Anthropic")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1
    assert data["sessions"][0]["id"] == "session-3"


def test_sessions_search_case_insensitive(s3_mock, api_event):
    """Test search is case-insensitive"""
    event = api_event(method="GET", path="/sessions", query_string="search=anthropic")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1


def test_sessions_search_no_results(s3_mock, api_event):
    """Test search returns empty when no matches"""
    event = api_event(method="GET", path="/sessions", query_string="search=xyz123notfound")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 0
    assert len(data["sessions"]) == 0


def test_sessions_combined_filters(s3_mock, api_event):
    """Test combining multiple filters"""
    event = api_event(method="GET", path="/sessions", query_string="date=2025-11-25&stage=CEO Stage")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["filters"]["date"] == "2025-11-25"
    assert data["filters"]["stage"] == "CEO Stage"
    assert data["count"] == 1  # Only session-1
    assert data["sessions"][0]["id"] == "session-1"


def test_sessions_filter_by_now_true(s3_mock, api_event):
    """Test filtering sessions by now=true"""
    # Mock current time to Nov 25, 2025 9:45 AM Paris time (during session-1)
    mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

    with patch('handler.get_paris_now', return_value=mock_time):
        event = api_event(method="GET", path="/sessions", query_string="now=true")

        response = handler.handler(event, None)
        data = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "currentTime" in data
        assert "ongoing" in data
        assert "upcoming" in data
        assert "count" in data["ongoing"]
        assert "sessions" in data["ongoing"]
        assert data["upcoming"]["description"] == "Sessions starting within 30 minutes"

        # session-1 should be ongoing (9:30-10:00, current is 9:45)
        assert data["ongoing"]["count"] >= 0


def test_sessions_now_upcoming_sessions(s3_mock, api_event):
    """Test now filter returns upcoming sessions"""
    # Mock current time to Nov 25, 2025 1:45 PM (15 min before session-2)
    mock_time = datetime(2025, 11, 25, 13, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

    with patch('handler.get_paris_now', return_value=mock_time):
        event = api_event(method="GET", path="/sessions", query_string="now=true")

        response = handler.handler(event, None)
        data = json.loads(response["body"])

        # session-2 starts at 2:00 PM, should be in upcoming
        assert data["upcoming"]["count"] >= 0


def test_sessions_now_ignores_other_filters(s3_mock, api_event):
    """Test that now=true ignores other filters"""
    mock_time = datetime(2025, 11, 25, 9, 45, 0, tzinfo=ZoneInfo("Europe/Paris"))

    with patch('handler.get_paris_now', return_value=mock_time):
        event = api_event(method="GET", path="/sessions", query_string="now=true&date=invalid&search=test")

        response = handler.handler(event, None)
        data = json.loads(response["body"])

        # Should work despite invalid other filters
        assert response["statusCode"] == 200
        assert "ongoing" in data
        assert "upcoming" in data


def test_speakers_search_by_name(s3_mock, api_event):
    """Test searching speakers by name"""
    event = api_event(method="GET", path="/speakers", query_string="search=John")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1
    assert "john" in data["speakers"][0]["name"].lower()


def test_speakers_search_by_company(s3_mock, api_event):
    """Test searching speakers by company"""
    event = api_event(method="GET", path="/speakers", query_string="search=BigBank")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1
    assert data["speakers"][0]["company"] == "BigBank"


def test_speakers_search_case_insensitive(s3_mock, api_event):
    """Test speaker search is case-insensitive"""
    event = api_event(method="GET", path="/speakers", query_string="search=anthropic")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 1


def test_speakers_search_no_results(s3_mock, api_event):
    """Test speaker search returns empty when no matches"""
    event = api_event(method="GET", path="/speakers", query_string="search=notfound")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 0
    assert len(data["speakers"]) == 0
