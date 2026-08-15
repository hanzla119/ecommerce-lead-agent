import sys
from pathlib import Path
from mangum import Mangum

# Add project root and current dir to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dashboard.server import app

# Vercel Serverless / AWS Lambda Handler
handler = Mangum(app, lifespan="off")
app = app
