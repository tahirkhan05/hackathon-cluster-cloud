#!/usr/bin/env python
"""Test tasks poll endpoint."""
import requests
import json

url = "http://localhost:8000/api/tasks/poll"
payload = {"node_id": "test-node-123"}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    print(f"Headers: {response.headers}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
