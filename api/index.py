import sys
import traceback
from pathlib import Path

# Add project root and current dir to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dashboard.server import app
except Exception as e:
    err_msg = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="Error Handler")
    
    @app.get("/{full_path:path}")
    @app.post("/{full_path:path}")
    def catch_all(full_path: str):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Server Initialization Error on Vercel",
                "details": str(e),
                "traceback": err_msg,
                "sys_path": sys.path,
                "base_dir_contents": [str(p) for p in BASE_DIR.iterdir()] if BASE_DIR.exists() else "BASE_DIR not found"
            }
        )
