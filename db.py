import psycopg2

def connect():
    conn = psycopg2.connect(
        dbname="The Wave",             
        user="postgres",
        password="mouatezGustave#18", 
        host="localhost"
    )
    return conn