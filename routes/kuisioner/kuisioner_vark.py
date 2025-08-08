import MySQLdb.cursors
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql
import collections
# from utils.rl_utils import get_state_from_scores


kuisioner_vark_bp = Blueprint(
    "kuisioner_vark", __name__, url_prefix="/kuisioner/vark")


@kuisioner_vark_bp.route("/", methods=["GET"])
@login_required
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM kuisioner_vark ORDER BY id")
    questions = cursor.fetchall()
    cursor.close()
    return render_template("kuisioner/kuisioner_vark.html", questions=questions)


@kuisioner_vark_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil semua data pertanyaan lengkap (id dan tipe)
    cursor.execute(
        "SELECT id, tipe_a, tipe_b, tipe_c, tipe_d FROM kuisioner_vark")
    questions = cursor.fetchall()

    skor = {
        "Visual": 0,
        "Auditory": 0,
        "Reading": 0,
        "Kinesthetic": 0
    }

    for row in questions:
        qid = row['id']
        tipe_map = {
            'a': row['tipe_a'],
            'b': row['tipe_b'],
            'c': row['tipe_c'],
            'd': row['tipe_d'],
        }

        jawaban = request.form.get(f"q_{qid}")  # hasil: 'a' / 'b' / 'c' / 'd'
        if jawaban in tipe_map:
            tipe = tipe_map[jawaban]
            if tipe in skor:
                skor[tipe] += 1

    total = sum(skor.values())
    if total > 0:
        for k in skor:
            skor[k] = round((skor[k] / total) * 100)

    # Simpan ke tabel scores_vark
    cursor.execute("""
        INSERT INTO scores_vark (siswa_id, visual, auditory, reading, kinesthetic)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        current_user.id,
        skor["Visual"],
        skor["Auditory"],
        skor["Reading"],
        skor["Kinesthetic"]
    ))

    mysql.connection.commit()
    cursor.close()

    flash("Terima kasih! Jawaban kamu sudah disimpan.", "success")
    return redirect(url_for("user_dashboard.index"))
