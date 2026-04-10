import psycopg2

# Create connection
conn = psycopg2.connect(
    host="localhost",
    database="secure_files",
    user="hemang15",
    password=""   
)

# Create cursor
cursor = conn.cursor()