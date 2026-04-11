import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="metro.proxy.rlwy.net",
        user="root",
        password="YOUR_PASSWORD",
        database="railway",
        port=26996   # ✅ hardcoded fix
    )