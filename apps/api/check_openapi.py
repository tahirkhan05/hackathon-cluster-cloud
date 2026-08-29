#!/usr/bin/env python
"""Check OpenAPI schema for tasks endpoints."""
import requests

try:
    response = requests.get("http://localhost:8000/openapi.json")
    schema = response.json()
    
    print("Task endpoints in OpenAPI schema:")
    for path, methods in schema["paths"].items():
        if "tasks" in path:
            print(f"  {path}")
            for method, details in methods.items():
                print(f"    {method.upper()}: {details.get('summary', 'No summary')}")
except Exception as e:
    print(f"Error: {e}")
