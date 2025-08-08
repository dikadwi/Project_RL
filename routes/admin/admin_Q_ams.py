# routes/admin_Q_ams.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql

admin_q_ams = Blueprint('admin_q_ams', __name__, url_prefix='/admin/q_ams')


@admin_q_ams.route('/')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM kuisioner_ams")
    kuisioner = cur.fetchall()
    cur.close()
    return render_template('admin/admin_Q_ams.html', kuisioner=kuisioner)


@admin_q_ams.route('/add_or_edit', methods=['POST'])
@login_required
def add_or_edit():
    id = request.form.get('id')
    pertanyaan = request.form['pertanyaan']
    opsi_a = request.form['opsi_a']
    opsi_b = request.form['opsi_b']
    opsi_c = request.form['opsi_c']
    opsi_d = request.form['opsi_d']
    kategori = request.form['kategori']

    cur = mysql.connection.cursor()
    if id:
        cur.execute("""
            UPDATE kuisioner_ams SET 
                pertanyaan=%s, opsi_a=%s, opsi_b=%s, opsi_c=%s, opsi_d=%s, kategori=%s
            WHERE id=%s
        """, (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori, id))
        flash('Pertanyaan berhasil diperbarui', 'success')
    else:
        cur.execute("""
            INSERT INTO kuisioner_ams 
                (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, kategori))
        flash('Pertanyaan berhasil ditambahkan', 'success')
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('admin_q_ams.index'))


@admin_q_ams.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM kuisioner_ams WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Pertanyaan berhasil dihapus', 'success')
    return redirect(url_for('admin_q_ams.index'))
