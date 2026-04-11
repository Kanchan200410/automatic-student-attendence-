import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="2005",   # 🔥 change this
        database="attendance_db",
        port=3306
    )