import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",   # 🔥 change this
        database="attendance_db",
        port=3306
    )