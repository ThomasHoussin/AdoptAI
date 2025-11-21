"""
AdoptAI API Lambda Handler
REST API for Adopt AI Grand Palais conference schedule
"""

import json
import os
import boto3
from typing import Any
from urllib.parse import parse_qs
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Global cache for data
_sessions_cache: list[dict] | None = None
_speakers_cache: list[dict] | None = None
_llms_txt_cache: str | None = None

# Environment variables
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")
DATA_PREFIX = os.environ.get("DATA_PREFIX", "data")

s3_client = boto3.client("s3")


def load_json_from_s3(key: str) -> dict:
    """Load JSON file from S3"""
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        raise RuntimeError(f"S3 error ({error_code}) loading {key}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {key}") from e


def get_sessions() -> list[dict]:
    """Get sessions data with caching and pre-parsed datetimes"""
    global _sessions_cache
    if _sessions_cache is None:
        data = load_json_from_s3(f"{DATA_PREFIX}/sessions.json")
        sessions = data.get("sessions", [])

        # Pre-parse all session datetimes for better performance with SnapStart
        # This happens once per Lambda instance and is cached across invocations
        for session in sessions:
            session["_start_dt"] = parse_session_datetime(
                session.get("date", ""),
                session.get("startTime", "")
            )
            session["_end_dt"] = parse_session_datetime(
                session.get("date", ""),
                session.get("endTime", "")
            )

        _sessions_cache = sessions
    return _sessions_cache


def get_speakers() -> list[dict]:
    """Get speakers data with caching"""
    global _speakers_cache
    if _speakers_cache is None:
        data = load_json_from_s3(f"{DATA_PREFIX}/speakers.json")
        _speakers_cache = data.get("speakers", [])
    return _speakers_cache


def get_llms_txt() -> str:
    """Get llms.txt content"""
    global _llms_txt_cache
    if _llms_txt_cache is None:
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f"{DATA_PREFIX}/llms.txt")
            _llms_txt_cache = response["Body"].read().decode("utf-8")
        except Exception as e:
            # Don't cache fallback - allow retry on next invocation
            print(f"Error loading llms.txt: {e}")
            return "# AdoptAI API\n\nVisit /sessions or /speakers for data."
    return _llms_txt_cache


def parse_time(time_str: str) -> int:
    """Parse time string to minutes since midnight"""
    try:
        time_str = time_str.strip().upper()
        if "AM" in time_str or "PM" in time_str:
            parts = time_str.replace("AM", "").replace("PM", "").strip().split(":")
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            if "PM" in time_str and hours != 12:
                hours += 12
            elif "AM" in time_str and hours == 12:
                hours = 0
            return hours * 60 + minutes
    except Exception:
        pass
    return 0


def parse_session_datetime(date_str: str, time_str: str) -> datetime | None:
    """Parse session date and time to datetime in Paris timezone"""
    try:
        # Parse date: "Nov 25, 2025" -> datetime
        date_str = date_str.strip()
        time_str = time_str.strip().upper()

        # Parse time
        parts = time_str.replace("AM", "").replace("PM", "").strip().split(":")
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0

        if "PM" in time_str and hours != 12:
            hours += 12
        elif "AM" in time_str and hours == 12:
            hours = 0

        # Parse date and combine with time
        dt = datetime.strptime(date_str, "%b %d, %Y")
        dt = dt.replace(hour=hours, minute=minutes, second=0, microsecond=0, tzinfo=ZoneInfo("Europe/Paris"))

        return dt
    except Exception:
        return None


def get_paris_now() -> datetime:
    """Get current time in Paris timezone"""
    return datetime.now(ZoneInfo("Europe/Paris"))


def filter_sessions_by_now(sessions: list[dict]) -> dict:
    """Filter sessions happening now or starting soon (within 30 minutes)

    Uses pre-parsed datetimes (_start_dt, _end_dt) cached in session objects.
    This optimization leverages SnapStart caching for better performance.
    """
    now = get_paris_now()
    in_30_min = now + timedelta(minutes=30)

    ongoing = []
    upcoming = []

    for session in sessions:
        # Use pre-parsed datetimes from cache (set in get_sessions())
        start_dt = session.get("_start_dt")
        end_dt = session.get("_end_dt")

        if not start_dt:
            continue

        # If no valid end time, assume session is still ongoing if it started recently
        if not end_dt or end_dt <= start_dt:
            # Fallback: assume session lasts 20 minutes (median gap from analysis)
            end_dt = start_dt + timedelta(minutes=20)

        # Check if session is ongoing
        if start_dt <= now <= end_dt:
            ongoing.append(session)
        # Check if session starts within 30 minutes
        elif start_dt > now and start_dt <= in_30_min:
            upcoming.append(session)

    return {
        "ongoing": ongoing,
        "upcoming": upcoming,
    }


def filter_sessions(sessions: list[dict], params: dict) -> list[dict]:
    """Filter sessions based on query parameters"""
    filtered = sessions.copy()

    # Filter by date
    date_filter = params.get("date", [None])[0]
    if date_filter:
        filtered = [
            s for s in filtered
            if date_filter in s.get("date", "") or
               (date_filter == "2025-11-25" and "Nov 25" in s.get("date", "")) or
               (date_filter == "2025-11-26" and "Nov 26" in s.get("date", ""))
        ]

    # Filter by stage
    stage_filter = params.get("stage", [None])[0]
    if stage_filter:
        filtered = [
            s for s in filtered
            if stage_filter.lower() in s.get("stage", "").lower()
        ]

    # Filter by time of day
    time_filter = params.get("time", [None])[0]
    if time_filter:
        if time_filter.lower() == "morning":
            filtered = [
                s for s in filtered
                if parse_time(s.get("startTime", "12:00 PM")) < 720
            ]
        elif time_filter.lower() == "afternoon":
            filtered = [
                s for s in filtered
                if parse_time(s.get("startTime", "0:00 AM")) >= 720
            ]

    # Full-text search
    search_filter = params.get("search", [None])[0]
    if search_filter:
        search_lower = search_filter.lower()
        filtered = [
            s for s in filtered
            if search_lower in s.get("title", "").lower() or
               any(
                   search_lower in sp.get("name", "").lower() or
                   search_lower in sp.get("company", "").lower() or
                   search_lower in sp.get("title", "").lower()
                   for sp in s.get("speakers", [])
               ) or
               any(search_lower in eco.lower() for eco in s.get("ecosystems", []))
        ]

    return filtered


def filter_speakers(speakers: list[dict], params: dict) -> list[dict]:
    """Filter speakers based on query parameters"""
    filtered = speakers.copy()

    search_filter = params.get("search", [None])[0]
    if search_filter:
        search_lower = search_filter.lower()
        filtered = [
            sp for sp in filtered
            if search_lower in sp.get("name", "").lower() or
               search_lower in sp.get("company", "").lower() or
               search_lower in sp.get("title", "").lower()
        ]

    return filtered


def create_response(status_code: int, body: Any, content_type: str = "application/json") -> dict:
    """Create HTTP response"""
    if content_type == "application/json":
        body_str = json.dumps(body, ensure_ascii=False)
        content_type_header = "application/json; charset=utf-8"
    else:
        body_str = str(body)
        content_type_header = f"{content_type}; charset=utf-8"

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": content_type_header,
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": body_str,
    }


def handler(event: dict, context: Any) -> dict:
    """Main Lambda handler"""

    request_context = event.get("requestContext", {})
    http = request_context.get("http", {})
    method = http.get("method", "GET")
    path = http.get("path", "/")

    if method == "OPTIONS":
        return create_response(200, "")

    query_string = event.get("rawQueryString", "")
    params = parse_qs(query_string)

    if path in ["/", "/llms.txt"]:
        return create_response(200, get_llms_txt(), "text/plain")

    elif path == "/robots.txt":
        robots_txt = "User-agent: *\nAllow: /\n"
        return create_response(200, robots_txt, "text/plain")

    elif path == "/health":
        return create_response(200, {"status": "healthy", "service": "adoptai-api"})

    elif path == "/sessions":
        sessions = get_sessions()

        # Check if 'now' parameter is present
        now_param = params.get("now", [None])[0]

        if now_param and now_param.lower() in ["true", "1", "yes"]:
            # Filter sessions happening now or starting soon
            now_filtered = filter_sessions_by_now(sessions)

            def format_session(session):
                start = session.get("startTime", "")
                end = session.get("endTime", "")
                time_str = f"{start} - {end}".strip(" -") if start or end else ""
                return {
                    "id": session.get("id", ""),
                    "title": session.get("title", ""),
                    "date": session.get("date", ""),
                    "time": time_str,
                    "stage": session.get("stage", ""),
                    "speakers": session.get("speakers", []),
                    "ecosystems": session.get("ecosystems", []),
                }

            paris_now = get_paris_now()

            return create_response(200, {
                "currentTime": paris_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "ongoing": {
                    "count": len(now_filtered["ongoing"]),
                    "sessions": [format_session(s) for s in now_filtered["ongoing"]],
                },
                "upcoming": {
                    "count": len(now_filtered["upcoming"]),
                    "description": "Sessions starting within 30 minutes",
                    "sessions": [format_session(s) for s in now_filtered["upcoming"]],
                },
            })
        else:
            # Regular filtering
            filtered = filter_sessions(sessions, params)

            formatted_sessions = []
            for session in filtered:
                start = session.get("startTime", "")
                end = session.get("endTime", "")
                time_str = f"{start} - {end}".strip(" -") if start or end else ""

                formatted_session = {
                    "id": session.get("id", ""),
                    "title": session.get("title", ""),
                    "date": session.get("date", ""),
                    "time": time_str,
                    "stage": session.get("stage", ""),
                    "speakers": session.get("speakers", []),
                    "ecosystems": session.get("ecosystems", []),
                }
                formatted_sessions.append(formatted_session)

            return create_response(200, {
                "total": len(sessions),
                "count": len(formatted_sessions),
                "filters": {k: v[0] for k, v in params.items() if v},
                "sessions": formatted_sessions,
            })

    elif path == "/speakers":
        speakers = get_speakers()
        filtered = filter_speakers(speakers, params)

        return create_response(200, {
            "count": len(filtered),
            "speakers": filtered,
        })

    else:
        return create_response(404, {
            "error": "Not Found",
            "message": f"Path {path} not found",
            "available_endpoints": ["/", "/llms.txt", "/robots.txt", "/sessions", "/speakers", "/health"],
        })
