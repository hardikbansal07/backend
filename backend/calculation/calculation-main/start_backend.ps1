# Starts FastAPI backend with correct module path and Swiss Ephemeris data path
$env:PYTHONPATH = "${PSScriptRoot}"
$env:SE_EPHE_PATH = "${PSScriptRoot}\src\jhora\data\ephe"
uvicorn src.api.app:app --host 127.0.0.1 --port 8080 --log-level info
