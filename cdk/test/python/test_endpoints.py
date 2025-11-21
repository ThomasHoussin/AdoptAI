"""Tests for API endpoints"""

import json
import pytest
import handler


def test_root_endpoint_returns_llms_txt(s3_mock, api_event):
    """Test GET / returns llms.txt content"""
    event = api_event(method="GET", path="/")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert "text/plain" in response["headers"]["Content-Type"]
    assert "charset=utf-8" in response["headers"]["Content-Type"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "240+ sessions" in response["body"]
    assert "•" in response["body"]  # UTF-8 check


def test_llms_txt_endpoint(s3_mock, api_event):
    """Test GET /llms.txt returns same as /"""
    root_event = api_event(method="GET", path="/")
    llms_event = api_event(method="GET", path="/llms.txt")

    root_response = handler.handler(root_event, None)
    llms_response = handler.handler(llms_event, None)

    assert root_response["body"] == llms_response["body"]
    assert llms_response["statusCode"] == 200


def test_robots_txt_endpoint(s3_mock, api_event):
    """Test GET /robots.txt returns robots.txt"""
    event = api_event(method="GET", path="/robots.txt")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert "text/plain" in response["headers"]["Content-Type"]
    assert "User-agent: *" in response["body"]
    assert "Allow: /" in response["body"]


def test_health_endpoint(s3_mock, api_event):
    """Test GET /health returns healthy status"""
    event = api_event(method="GET", path="/health")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert "application/json" in response["headers"]["Content-Type"]
    assert "charset=utf-8" in response["headers"]["Content-Type"]

    data = json.loads(response["body"])
    assert data == {
        "status": "healthy",
        "service": "adoptai-api"
    }


def test_sessions_endpoint_no_filters(s3_mock, api_event):
    """Test GET /sessions returns all sessions"""
    event = api_event(method="GET", path="/sessions")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert "application/json" in response["headers"]["Content-Type"]
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"

    data = json.loads(response["body"])
    assert "total" in data
    assert "count" in data
    assert "sessions" in data
    assert data["total"] == 3
    assert data["count"] == 3
    assert len(data["sessions"]) == 3

    # Check session structure
    session = data["sessions"][0]
    assert "id" in session
    assert "title" in session
    assert "date" in session
    assert "time" in session
    assert "stage" in session
    assert "speakers" in session
    assert "ecosystems" in session


def test_speakers_endpoint_no_filters(s3_mock, api_event):
    """Test GET /speakers returns all speakers"""
    event = api_event(method="GET", path="/speakers")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert "application/json" in response["headers"]["Content-Type"]

    data = json.loads(response["body"])
    assert "count" in data
    assert "speakers" in data
    assert data["count"] == 2
    assert len(data["speakers"]) == 2

    # Check speaker structure
    speaker = data["speakers"][0]
    assert "name" in speaker
    assert "company" in speaker


def test_404_for_unknown_path(s3_mock, api_event):
    """Test GET /unknown returns 404"""
    event = api_event(method="GET", path="/unknown-path")

    response = handler.handler(event, None)

    assert response["statusCode"] == 404
    assert "application/json" in response["headers"]["Content-Type"]

    data = json.loads(response["body"])
    assert data["error"] == "Not Found"
    assert "message" in data
    assert "available_endpoints" in data
    assert "/sessions" in data["available_endpoints"]


def test_options_request_returns_cors(s3_mock, api_event):
    """Test OPTIONS /sessions returns CORS headers"""
    event = api_event(method="OPTIONS", path="/sessions")

    response = handler.handler(event, None)

    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"
    assert "GET" in response["headers"]["Access-Control-Allow-Methods"]


def test_json_encoding_preserves_utf8(s3_mock, api_event):
    """Test that JSON responses preserve UTF-8 characters"""
    event = api_event(method="GET", path="/sessions")

    response = handler.handler(event, None)

    # The response body should be valid JSON with UTF-8
    data = json.loads(response["body"])

    # Re-encode to ensure no ASCII escape sequences
    body_str = json.dumps(data, ensure_ascii=False)

    # Should not contain ASCII escape sequences like \u00e9
    assert "\\u" not in body_str or "\\u0" not in response["body"]


def test_no_internal_fields_exposed(s3_mock, api_event):
    """Test that internal cache fields are not exposed in responses"""
    event = api_event(method="GET", path="/sessions")

    response = handler.handler(event, None)
    data = json.loads(response["body"])

    # Internal fields should not be in response
    for session in data["sessions"]:
        assert "_start_dt" not in session
        assert "_end_dt" not in session
