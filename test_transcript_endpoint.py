#!/usr/bin/env python3
"""
Quick test script to test the /transcripts/process endpoint with minimal input.
"""
import requests
import json

# API endpoint
url = "http://127.0.0.1:8000/transcripts/process"

# Minimal meeting details
meeting_details = {
    "meeting_date": "2023-10-27T10:00:00Z",
    "meeting_type": "Test Meeting",
    "attendees": ["Alice"]
}

# Create a very small transcript file
transcript_content = b"Alice: Let's test this API. Bob: Sounds good."

# Prepare the request
files = {
    "file": ("test.txt", transcript_content, "text/plain")
}

data = {
    "meeting_details": json.dumps(meeting_details)
}

print("Testing /transcripts/process endpoint...")
print(f"Transcript size: {len(transcript_content)} bytes")
print(f"Meeting details: {meeting_details}")
print()

try:
    response = requests.post(url, files=files, data=data, timeout=30)

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()

    if response.status_code == 200:
        print("✅ Success!")
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
