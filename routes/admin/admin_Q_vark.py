# routes/admin_Q_vark.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql
import MySQLdb.cursors

admin_q_vark = Blueprint('admin_q_vark', __name__, url_prefix='/admin/q_vark')


@admin_q_vark.route('/')
@login_required
def index():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM kuisioner_vark ORDER BY id ASC")
    kuisioner = cursor.fetchall()
    cursor.close()
    return render_template('admin/admin_Q_vark.html', kuisioner=kuisioner)


@admin_q_vark.route('/add_or_edit', methods=['POST'])
@login_required
def add_or_edit():
    if current_user.role != 'admin':
        return "Unauthorized", 403

    id = request.form.get('id')
    pertanyaan = request.form['pertanyaan']
    opsi_a = request.form['opsi_a']
    tipe_a = request.form['tipe_a']
    opsi_b = request.form['opsi_b']
    tipe_b = request.form['tipe_b']
    opsi_c = request.form['opsi_c']
    tipe_c = request.form['tipe_c']
    opsi_d = request.form['opsi_d']
    tipe_d = request.form['tipe_d']

    cursor = mysql.connection.cursor()

    if id:
        # Edit
        cursor.execute("""
            UPDATE kuisioner_vark
            SET pertanyaan=%s, opsi_a=%s, tipe_a=%s,
                opsi_b=%s, tipe_b=%s, opsi_c=%s, tipe_c=%s,
                opsi_d=%s, tipe_d=%s
            WHERE id=%s
        """, (pertanyaan, opsi_a, tipe_a, opsi_b, tipe_b,
              opsi_c, tipe_c, opsi_d, tipe_d, id))
    else:
        # Tambah
        cursor.execute("""
            INSERT INTO kuisioner_vark
            (pertanyaan, opsi_a, tipe_a, opsi_b, tipe_b,
             opsi_c, tipe_c, opsi_d, tipe_d)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (pertanyaan, opsi_a, tipe_a, opsi_b, tipe_b,
              opsi_c, tipe_c, opsi_d, tipe_d))

    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('admin_q_vark.index'))


@admin_q_vark.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        return "Unauthorized", 403

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM kuisioner_vark WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Pertanyaan berhasil dihapus.")
    return redirect(url_for('admin_q_vark.index'))
