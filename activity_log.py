from db import mysql
from datetime import datetime


def log_activity(user_id, type, description, start_time, end_time):
    duration = int((end_time - start_time).total_seconds())
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO activity_log (user_id, type, description, start_time, end_time, duration_seconds)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, type, description, start_time, end_time, duration))
    mysql.connection.commit()
    cursor.close()
