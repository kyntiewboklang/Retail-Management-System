import psycopg2

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="RMSDB",
        user="postgres",
        password="1234"
    )
    return conn