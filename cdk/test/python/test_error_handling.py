"""Tests for error handling"""

import json
import pytest
from unittest.mock import patch
from botocore.exceptions import ClientError
import handler


def test_load_json_from_s3_handles_client_error(s3_mock):
    """Test S3 ClientError is properly handled"""
    with pytest.raises(RuntimeError) as exc_info:
        handler.load_json_from_s3("data/nonexistent.json")

    assert "S3 error" in str(exc_info.value)


def test_load_json_from_s3_handles_invalid_json(s3_mock, monkeypatch):
    """Test invalid JSON is properly handled"""
    import boto3

    monkeypatch.setenv("BUCKET_NAME", "test-adoptai-bucket")

    # Put invalid JSON
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.put_object(
        Bucket="test-adoptai-bucket",
        Key="data/invalid.json",
        Body=b"{ invalid json }"
    )

    with pytest.raises(RuntimeError) as exc_info:
        handler.load_json_from_s3("data/invalid.json")

    assert "Invalid JSON" in str(exc_info.value)


def test_llms_txt_fallback_on_error(s3_mock, api_event):
    """Test fallback message when llms.txt cannot be loaded"""
    # Delete llms.txt to cause error
    import boto3
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_client.delete_object(Bucket="test-adoptai-bucket", Key="data/llms.txt")

    # Reset cache
    handler._llms_txt_cache = None

    event = api_event(method="GET", path="/")
    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    body = response["body"]
    assert "AdoptAI API" in body
    assert "Visit /sessions or /speakers" in body


def test_get_sessions_caching(s3_mock):
    """Test that sessions are cached after first load"""
    # First call - loads from S3
    sessions1 = handler.get_sessions()

    # Verify cache is populated
    assert handler._sessions_cache is not None
    assert len(sessions1) == 3

    # Second call - uses cache
    sessions2 = handler.get_sessions()

    # Should return same cached instance
    assert sessions1 is sessions2


def test_get_sessions_adds_parsed_datetimes(s3_mock):
    """Test that get_sessions adds _start_dt and _end_dt to sessions"""
    sessions = handler.get_sessions()

    for session in sessions:
        assert "_start_dt" in session
        assert "_end_dt" in session

        # Should be datetime objects or None
        if session["_start_dt"] is not None:
            from datetime import datetime
            assert isinstance(session["_start_dt"], datetime)


def test_get_speakers_caching(s3_mock):
    """Test that speakers are cached after first load"""
    # First call - loads from S3
    speakers1 = handler.get_speakers()

    # Verify cache is populated
    assert handler._speakers_cache is not None
    assert len(speakers1) == 2

    # Second call - uses cache
    speakers2 = handler.get_speakers()

    # Should return same cached instance
    assert speakers1 is speakers2


def test_get_llms_txt_caching(s3_mock):
    """Test that llms.txt is cached after first load"""
    # First call - loads from S3
    content1 = handler.get_llms_txt()

    # Verify cache is populated
    assert handler._llms_txt_cache is not None

    # Second call - uses cache
    content2 = handler.get_llms_txt()

    # Should return same cached string
    assert content1 == content2


def test_filter_sessions_with_missing_fields(s3_mock):
    """Test filtering sessions that have missing fields"""
    sessions = [
        {"id": "1", "title": "Test"},  # Missing date, stage, speakers
        {"id": "2", "title": "Test 2", "date": "Nov 25", "stage": "CEO Stage"},
    ]

    # Should not crash with missing fields
    result = handler.filter_sessions(sessions, {"date": ["Nov 25"]})

    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_filter_speakers_with_missing_fields(s3_mock):
    """Test filtering speakers that have missing fields"""
    speakers = [
        {"name": "John"},  # Missing company, role
        {"name": "Jane", "company": "Acme", "role": "CEO"},
    ]

    # Should not crash with missing fields
    result = handler.filter_speakers(speakers, {"search": ["Acme"]})

    assert len(result) == 1
    assert result[0]["name"] == "Jane"


def test_empty_query_string_params(s3_mock, api_event):
    """Test handling of empty query string parameters"""
    event = api_event(method="GET", path="/sessions", query_string="")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert data["count"] == 3  # All sessions


def test_malformed_query_string(s3_mock, api_event):
    """Test handling of malformed query strings"""
    event = api_event(method="GET", path="/sessions", query_string="invalid&&&")

    response = handler.handler(event, None)

    # Should not crash
    assert response["statusCode"] == 200


def test_session_with_no_speakers(s3_mock, api_event):
    """Test sessions with empty speakers array"""
    event = api_event(method="GET", path="/sessions")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    # session-2 has no speakers
    session_2 = next((s for s in data["sessions"] if s["id"] == "session-2"), None)
    assert session_2 is not None
    assert session_2["speakers"] == []


def test_create_response_with_non_json_content_type(s3_mock):
    """Test create_response with text/plain content type"""
    response = handler.create_response(200, "Hello World", "text/plain")

    assert response["statusCode"] == 200
    assert "text/plain" in response["headers"]["Content-Type"]
    assert "charset=utf-8" in response["headers"]["Content-Type"]
    assert response["body"] == "Hello World"


def test_create_response_preserves_utf8_in_json(s3_mock):
    """Test create_response preserves UTF-8 characters in JSON"""
    data = {"message": "Hello • World"}

    response = handler.create_response(200, data, "application/json")

    assert response["statusCode"] == 200
    assert "application/json" in response["headers"]["Content-Type"]
    assert "charset=utf-8" in response["headers"]["Content-Type"]

    # Verify UTF-8 character is preserved
    body = json.loads(response["body"])
    assert body["message"] == "Hello • World"
    assert "•" in response["body"]
