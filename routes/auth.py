from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from db import mysql
from models.user import User
import MySQLdb.cursors

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # ✅ Cek tabel users (admin/user)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and user['password'] == password and user.get('id') and user.get('role'):
            role = user.get('role')  # 'admin' atau 'user'
            print("Login berhasil:", user)  # ← Tambahkan ini
            print("Role:", role)
            print("ID:", user.get('id'))
            login_user(User(user, role))
            # ⬅️ Biarkan dashboard yang arahkan
            return redirect(url_for('dashboard.index'))

        # ✅ Cek tabel siswa (TIDAK DIUBAH)
        cursor.execute(
            "SELECT * FROM siswa WHERE nama_lengkap = %s", (username,))
        siswa = cursor.fetchone()
        if siswa and siswa['password'] == password:
            login_user(User(siswa, 'siswa'))
            return redirect(url_for('user_dashboard.index'))

        flash('Login gagal. Username atau password salah.')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
