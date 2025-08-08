import MySQLdb.cursors
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from db import mysql
# from utils.rl_utils import get_state_from_scores


kuisioner_mlsq_bp = Blueprint(
    "kuisioner_mlsq", __name__, url_prefix="/kuisioner/mlsq")


@kuisioner_mlsq_bp.route("/", methods=["GET"])
@login_required
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM kuisioner_mlsq ORDER BY id")
    questions = cursor.fetchall()
    cursor.close()
    return render_template("kuisioner/kuisioner_mlsq.html", questions=questions)


@kuisioner_mlsq_bp.route("/submit", methods=["POST"])
@login_required
def submit():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil pertanyaan untuk kategori
    cursor.execute("SELECT id, kategori FROM kuisioner_mlsq")
    data = cursor.fetchall()

    skor = {
        "self_regulation": 0,
        "task_value": 0,
        "control_belief": 0,
        "goal_orientation": 0,
        "self_efficacy": 0
    }

    max_per_kategori = {
        "self_regulation": 0,
        "task_value": 0,
        "control_belief": 0,
        "goal_orientation": 0,
        "self_efficacy": 0
    }

    for row in data:
        qid = row['id']
        kategori = row['kategori']
        jawaban = request.form.get(f"jawaban_{qid}")
        if jawaban:
            try:
                skor[kategori] += int(jawaban)
                max_per_kategori[kategori] += 7
            except:
                pass

    # Simpan ke tabel
    cursor.execute("""
        INSERT INTO scores_mlsq (siswa_id, self_regulation, task_value, control_belief, goal_orientation, self_efficacy)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        current_user.id,
        skor["self_regulation"],
        skor["task_value"],
        skor["control_belief"],
        skor["goal_orientation"],
        skor["self_efficacy"]
    ))

    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("user_dashboard.index"))
