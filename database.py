import os
import mysql.connector
from urllib.parse import urlparse

def get_db_connection():
    url = os.getenv("MYSQL_URL")

    result = urlparse(url)

    return mysql.connector.connect(
        host=result.hostname,
        user=result.username,
        password=result.password,
        database=result.path[1:],
        port=result.port
    )