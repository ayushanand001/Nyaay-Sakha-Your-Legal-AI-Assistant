import psycopg
from app.core.config import settings

def get_connection():
    if not settings.DATABASE_URL:
        raise RuntimeError("SUPABASE_DB / DATABASE_URL connection string is not configured in environment.")
    return psycopg.connect(settings.DATABASE_URL)
