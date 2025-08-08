from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql
import MySQLdb.cursors

admin_q_mlsq = Blueprint('admin_q_mlsq', __name__, url_prefix='/admin/q_mlsq')


@admin_q_mlsq.route('/')
@login_required
def index():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM kuisioner_mlsq ORDER BY id ASC")
    kuisioner = cursor.fetchall()
    cursor.close()
    return render_template('admin/admin_Q_mlsq.html', kuisioner=kuisioner)


@admin_q_mlsq.route('/add_or_edit', methods=['POST'])
@login_required
def add_or_edit():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    id = request.form.get('id')
    pertanyaan = request.form['pertanyaan']
    opsi_a = request.form['opsi_a']
    opsi_b = request.form['opsi_b']
    opsi_c = request.form['opsi_c']
    opsi_d = request.form['opsi_d']
    kategori = request.form['kategori']

    cursor = mysql.connection.cursor()

    if id:
        # Edit
        cursor.execute("""
            UPDATE kuisioner_mlsq
            SET pertanyaan=%s, opsi_a=%s, opsi_b=%s, opsi_c=%s, opsi_d=%s, kategori=%s
            WHERE id=%s
        """, (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori, id))
    else:
        # Tambah
        cursor.execute("""
            INSERT INTO kuisioner_mlsq (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori))

    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('admin_q_mlsq.index'))


@admin_q_mlsq.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM kuisioner_mlsq WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Pertanyaan berhasil dihapus.")
    return redirect(url_for('admin_q_mlsq.index'))
