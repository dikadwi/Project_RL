from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from db import mysql

admin_siswa_bp = Blueprint('admin_siswa', __name__, url_prefix="/admin/siswa")


@admin_siswa_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if current_user.role != "admin":
        return "Unauthorized", 403

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM siswa")
    siswa_data = cursor.fetchall()
    cursor.close()
    return render_template("admin/admin_siswa_list.html", siswa_list=siswa_data)


@admin_siswa_bp.route("/tambah", methods=["POST"])
@login_required
def tambah():
    if current_user.role != "admin":
        return "Unauthorized", 403

    nama = request.form["nama_lengkap"]
    kelas = request.form["kelas"]
    jk = request.form["jenis_kelamin"]
    email = request.form["email"]

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO siswa (nama_lengkap, kelas, jenis_kelamin, email) VALUES (%s, %s, %s, %s)",
                   (nama, kelas, jk, email))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("admin_siswa.index"))


@admin_siswa_bp.route("/edit/<int:id>", methods=["POST"])
@login_required
def edit(id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    nama = request.form["nama_lengkap"]
    kelas = request.form["kelas"]
    jk = request.form["jenis_kelamin"]
    email = request.form["email"]

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE siswa SET nama_lengkap=%s, kelas=%s, jenis_kelamin=%s, email=%s WHERE siswa_id=%s",
                   (nama, kelas, jk, email, id))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("admin_siswa.index"))


@admin_siswa_bp.route("/hapus/<int:id>")
@login_required
def hapus(id):
    if current_user.role != "admin":
        return "Unauthorized", 403

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM siswa WHERE siswa_id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("admin_siswa.index"))
