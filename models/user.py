from flask_login import UserMixin
from db import mysql
import MySQLdb.cursors


class User(UserMixin):
    def __init__(self, data, role):
        self.id = data.get('id') or data.get('siswa_id')  # support kedua tabel
        self.username = data.get('username') or data.get('nama_lengkap')
        self.role = role

    def get_id(self):
        return f"{self.role}:{self.id}"  # format: 'user:1' atau 'siswa:5'

    @property
    def from_siswa(self):
        return self.role == 'siswa'  # bisa dipakai di template

# Fungsi load_user untuk Flask-Login


def load_user(user_id):
    try:
        print("Received user_id:", user_id)
        role, real_id = user_id.split(":")
        print("Role:", role, "Real ID:", real_id)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if role == 'user':
            cursor.execute("SELECT * FROM users WHERE id = %s", (real_id,))
            data = cursor.fetchone()
            cursor.close()
            return User(data, 'user') if data else None

        elif role == 'admin':
            cursor.execute("SELECT * FROM users WHERE id = %s", (real_id,))
            data = cursor.fetchone()
            cursor.close()
            return User(data, 'admin') if data else None

        elif role == 'siswa':
            cursor.execute(
                "SELECT * FROM siswa WHERE siswa_id = %s", (real_id,))
            data = cursor.fetchone()
            cursor.close()
            return User(data, 'siswa') if data else None

    except Exception as e:
        print("Error in load_user:", e)
        return None
