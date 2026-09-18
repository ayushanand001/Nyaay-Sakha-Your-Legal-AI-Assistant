import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SUPABASE_DB")
def get_connection():
    return psycopg.connect(DATABASE_URL)

