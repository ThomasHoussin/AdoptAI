"""Pytest fixtures for Lambda handler tests"""

import json
import os
import pytest
import boto3
from moto import mock_aws


@pytest.fixture
def sample_sessions_data():
    """Sample sessions data for testing"""
    return {
        "metadata": {
            "scrapedAt": "2025-11-19T12:00:00Z",
            "totalSessions": 3
        },
        "sessions": [
            {
                "id": "session-1",
                "title": "AI in Banking",
                "date": "Nov 25, 2025",
                "startTime": "9:30 AM",
                "endTime": "10:00 AM",
                "stage": "CEO Stage",
                "speakers": [
                    {
                        "name": "John Doe",
                        "company": "BigBank",
                        "role": "CEO"
                    }
                ],
                "ecosystems": ["finance"]
            },
            {
                "id": "session-2",
                "title": "Cloud Infrastructure",
                "date": "Nov 25, 2025",
                "startTime": "2:00 PM",
                "endTime": "2:30 PM",
                "stage": "Mainstage South",
                "speakers": [],
                "ecosystems": ["cloud"]
            },
            {
                "id": "session-3",
                "title": "Future of AI",
                "date": "Nov 26, 2025",
                "startTime": "10:00 AM",
                "endTime": "10:30 AM",
                "stage": "CEO Stage",
                "speakers": [
                    {
                        "name": "Jane Smith",
                        "company": "Anthropic",
                        "role": "Researcher"
                    }
                ],
                "ecosystems": ["ai"]
            }
        ]
    }


@pytest.fixture
def sample_speakers_data():
    """Sample speakers data for testing"""
    return {
        "metadata": {
            "scrapedAt": "2025-11-19T12:00:00Z",
            "totalSpeakers": 2
        },
        "speakers": [
            {
                "name": "John Doe",
                "company": "BigBank",
                "title": "CEO",
                "sessions": ["session-1"]
            },
            {
                "name": "Jane Smith",
                "company": "Anthropic",
                "title": "Researcher",
                "sessions": ["session-3"]
            }
        ]
    }


@pytest.fixture
def sample_llms_txt():
    """Sample llms.txt content for testing"""
    return "# AdoptAI API\n\n240+ sessions • 200+ speakers\n\n## Endpoints\n\nGET /sessions\nGET /speakers"


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Setup environment variables and AWS credentials for all tests"""
    # AWS credentials for moto
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

    # Lambda environment variables
    monkeypatch.setenv("BUCKET_NAME", "test-adoptai-bucket")
    monkeypatch.setenv("DATA_PREFIX", "data")


@pytest.fixture
def s3_mock(sample_sessions_data, sample_speakers_data, sample_llms_txt):
    """Create a mock S3 bucket with test data

    Only activated when test explicitly uses this fixture.
    """
    with mock_aws():
        # Import handler INSIDE the mock context to ensure s3_client is mocked
        import handler

        # Force handler to use correct env vars (in case it was already imported)
        handler.BUCKET_NAME = "test-adoptai-bucket"
        handler.DATA_PREFIX = "data"

        # Recreate s3_client with mocked boto3
        handler.s3_client = boto3.client("s3", region_name="us-east-1")

        bucket_name = "test-adoptai-bucket"

        # Create bucket
        handler.s3_client.create_bucket(Bucket=bucket_name)

        # Upload test data
        handler.s3_client.put_object(
            Bucket=bucket_name,
            Key="data/sessions.json",
            Body=json.dumps(sample_sessions_data).encode("utf-8")
        )

        handler.s3_client.put_object(
            Bucket=bucket_name,
            Key="data/speakers.json",
            Body=json.dumps(sample_speakers_data).encode("utf-8")
        )

        handler.s3_client.put_object(
            Bucket=bucket_name,
            Key="data/llms.txt",
            Body=sample_llms_txt.encode("utf-8")
        )

        yield


@pytest.fixture
def api_event():
    """Sample Lambda event for API Gateway"""
    def _make_event(method="GET", path="/", query_string=""):
        return {
            "requestContext": {
                "http": {
                    "method": method,
                    "path": path
                }
            },
            "rawQueryString": query_string
        }
    return _make_event


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset global cache between tests"""
    import handler
    handler._sessions_cache = None
    handler._speakers_cache = None
    handler._llms_txt_cache = None
    yield
    handler._sessions_cache = None
    handler._speakers_cache = None
    handler._llms_txt_cache = None
