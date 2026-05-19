from fastapi.testclient import TestClient
import sys
import os

# Ensure backend is in path
sys.path.append(os.getcwd())

try:
    from backend.main import app
    client = TestClient(app)

    # Check Route Information
    routes = [route.path for route in app.routes]
    target_route = "/api/me/preferences"
    exists = target_route in routes
    print(f"Route {target_route} exists: {exists}")

    # GET Request
    print("--- GET /api/me/preferences ---")
    response_get = client.get(target_route)
    print(f"Status: {response_get.status_code}")
    print(f"Body: {response_get.text}")

    # POST Request
    print("--- POST /api/me/preferences ---")
    response_post = client.post(target_route, json={})
    print(f"Status: {response_post.status_code}")
    print(f"Body: {response_post.text}")

except Exception as e:
    print(f"Error during smoke test: {e}")
    import traceback
    traceback.print_exc()
