import sys
import os

# Helper to suppress logs
import logging
logging.disable(logging.CRITICAL)

try:
    from main import app
    print("SUCCESS: Successfully imported main.app")
except ImportError as e:
    print(f"ERROR: Failed to import main.app: {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error importing main.app: {e}")
    sys.exit(1)

# Check routes
found = False
for route in app.routes:
    if hasattr(route, "path") and route.path == "/api/admin/login":
        found = True
        print("SUCCESS: Found route /api/admin/login")
        break

if not found:
    print("ERROR: Route /api/admin/login not found in app.routes")
    # list all routes for debugging
    # for route in app.routes:
    #    if hasattr(route, "path"): print(route.path)
    sys.exit(1)

print("Verification passed.")
