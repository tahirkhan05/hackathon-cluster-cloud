import requests

url = "http://localhost:8000/api/tasks/poll"
payload = {"node_id": "test-node-123"}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
