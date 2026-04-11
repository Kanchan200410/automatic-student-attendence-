import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="2005",   # 🔥 change this
        database="student_db",
        port=3306
    )