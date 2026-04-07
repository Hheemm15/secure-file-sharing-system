import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="secure_files",
    user="hemang15",   
    password=""        
)

cursor = conn.cursor()