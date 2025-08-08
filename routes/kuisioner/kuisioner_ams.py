import MySQLdb.cursors
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql
# from utils.rl_utils import get_state_from_scores


kuisioner_ams_bp = Blueprint(
    "kuisioner_ams", __name__, url_prefix="/kuisioner/ams")


@kuisioner_ams_bp.route("/", methods=["GET"])
@login_required
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM kuisioner_ams ORDER BY id")
    questions = cursor.fetchall()
    cursor.close()
    return render_template("kuisioner/kuisioner_ams.html", questions=questions)


@kuisioner_ams_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT id, kategori FROM kuisioner_ams ORDER BY id")
    data = cursor.fetchall()

    skor = {
        "intrinsic": 0,
        "extrinsic": 0,
        "amotivation": 0
    }

    count = {
        "intrinsic": 0,
        "extrinsic": 0,
        "amotivation": 0
    }

    for row in data:
        qid = row['id']
        kategori = row['kategori']
        nilai = request.form.get(f"jawaban_{qid}")
        if nilai:
            skor[kategori] += int(nilai)
            count[kategori] += 1

    for k in skor:
        if count[k] > 0:
            skor[k] = round(skor[k] / count[k], 2)

    cursor.execute("""
        INSERT INTO scores_ams (siswa_id, intrinsic, extrinsic, amotivation)
        VALUES (%s, %s, %s, %s)
    """, (current_user.id, skor["intrinsic"], skor["extrinsic"], skor["amotivation"]))

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for("user_dashboard.index"))
