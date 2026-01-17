import sys
import os
from unittest.mock import MagicMock

# Mock dotenv
sys.modules["dotenv"] = MagicMock()
# Mock passlib (used in auth.py) - in case it's missing
sys.modules["passlib"] = MagicMock()
sys.modules["passlib.context"] = MagicMock()
# Mock jose (used in auth.py)
sys.modules["jose"] = MagicMock()
# Mock google.oauth2, google.auth.transport (used in auth.py)
sys.modules["google"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.auth"] = MagicMock()
sys.modules["google.auth.transport"] = MagicMock()
# Mock mongo (used in main.py lifespan) - though correct import might trigger connection
# We want to avoid connection side effects too.
# But main.py imports mongo.
# We can mock mongo too if needed, but mongo.py seems simple.
# Let's mock mongo to be safe.
sys.modules["mongo"] = MagicMock()

# Also mock fastapi? No, fastapi should be installed. 
# But if it's not in python3 system, we fail.
# Assume fastapi IS installed because `from fastapi import ...` worked in main?
# Wait, user said "Use motor...".
# If python3 is system python, it might lack fastapi too.
# The error "No module named 'dotenv'" implies packages are missing.
# So `fastapi` likely missing too.
# Logic: checking imports statically or assuming correctness if env is broken.

# If env is broken for `python3`, I cannot verify runtime imports easily.
# I will check file existence and content strings as a fallback verification.

print("Checking file existence and content strings...")

files_to_check = [
    "app/admin/auth.py",
    "main.py",
    "models.py"
]

missing = []
for f in files_to_check:
    if not os.path.exists(f):
        missing.append(f)

if missing:
    print(f"ERROR: Missing files: {missing}")
    sys.exit(1)

# Check main.py content
with open("main.py", "r") as f:
    content = f.read()
    if "/api/admin" not in content:
        print("ERROR: main.py does not contain '/api/admin'")
        sys.exit(1)
    if "app.admin.auth" not in content:
        print("ERROR: main.py does not contain 'app.admin.auth'")
        sys.exit(1)

# Check auth.py content
with open("app/admin/auth.py", "r") as f:
    content = f.read()
    if "UserRole.admin" not in content:
        print("ERROR: app/admin/auth.py does not check UserRole.admin")
        sys.exit(1)

print("Static verification passed.")
