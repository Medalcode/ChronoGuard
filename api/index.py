import os
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/chronoguard")
os.environ.setdefault("SECRET_KEY", "serverless-demo-secret-key-change-in-prod")
os.environ.setdefault("ENVIRONMENT", "production")

from app.main import app
from mangum import Mangum

handler = Mangum(app)
