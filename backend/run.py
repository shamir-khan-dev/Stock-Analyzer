import os
import sys
from pathlib import Path
import uvicorn

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("==================================================================")
    print("  [AlphaPulse] Institutional Quantitative Terminal (GO::OS)")
    print(f"  Local Access:   http://127.0.0.1:{port}")
    print(f"  Network/Cloud:  http://{host}:{port}")
    print(f"  API Docs:       http://127.0.0.1:{port}/docs")
    print("==================================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=False, workers=1)
