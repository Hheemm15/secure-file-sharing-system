import psycopg2

# Create connection
conn = psycopg2.connect(
    host="localhost",
    database="secure_files",
    user="postgres",
    password="5926"   
)

# Create cursor
cursor = conn.cursor()