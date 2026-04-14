import os
import psycopg2

def get_db_connection():
    DATABASE_URL = os.getenv("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL)