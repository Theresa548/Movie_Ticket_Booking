import mysql.connector

def get_db_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Theresa@123",
        database="movie_booking"
    )

    return conn