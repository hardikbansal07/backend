import sys
import os
sys.path.append(os.getcwd())

try:
    from routers.report_routes import router
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
