#!/usr/bin/env python3
"""
Test script for POST /transcripts/save endpoint
"""
import requests
import json

# API endpoint
url = "http://127.0.0.1:8000/transcripts/save"

# Load the gemini output as test data
with open("gemini_output.json", "r") as f:
    test_data = json.load(f)

print("Testing POST /transcripts/save endpoint...")
print(f"Meeting: {test_data.get('meeting_details', {})}")
print(f"Task groups: {len(test_data.get('task_groups', []))}")
print()

try:
    response = requests.post(url, json=test_data, timeout=30)

    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 201:
        print("✅ Success!")
        result = response.json()
        print(json.dumps(result, indent=2))
        print(f"\nMeeting ID: {result.get('meeting_id')}")
        print(f"Task count: {result.get('task_count')}")
        print(f"Planner sync: {result.get('planner_sync_status')}")
    else:
        print(f"❌ Error {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
