import os
import sys
import warnings

_DEFAULT_DB = "postgresql://user:pass@localhost:5432/chronoguard"
_DEFAULT_SECRET = "serverless-demo-secret-key-change-in-prod"

if os.environ.get("DATABASE_URL", _DEFAULT_DB) == _DEFAULT_DB:
    warnings.warn(
        "DATABASE_URL is using an insecure default. Set it via Vercel environment variables.",
        UserWarning,
    )

if os.environ.get("SECRET_KEY", _DEFAULT_SECRET) == _DEFAULT_SECRET:
    warnings.warn(
        "SECRET_KEY is using an insecure default. Set a strong random secret in production.",
        UserWarning,
    )

os.environ.setdefault("DATABASE_URL", _DEFAULT_DB)
os.environ.setdefault("SECRET_KEY", _DEFAULT_SECRET)
os.environ.setdefault("ENVIRONMENT", "production")

from mangum import Mangum

from app.main import app

handler = Mangum(app)
