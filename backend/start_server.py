"""
Unified Backend Server Startup Script
Production-ready server with proper configuration
"""
import os
import sys
import uvicorn
from pathlib import Path

# Ensure proper path setup
backend_dir = Path(__file__).parent
calculation_src = backend_dir / "calculation" / "calculation-main" / "src"

if str(calculation_src) not in sys.path:
    sys.path.insert(0, str(calculation_src))

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Astrology Backend Server...")
    print("=" * 60)
    print(f"Backend Directory: {backend_dir}")
    print(f"Calculation Source: {calculation_src}")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
