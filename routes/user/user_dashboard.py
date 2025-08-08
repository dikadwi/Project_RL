from flask import Blueprint, render_template
from flask import redirect, url_for
from db import mysql
import MySQLdb.cursors
from flask_login import login_required, current_user
# from flask_login import login_required

user_dashboard_bp = Blueprint(
    'user_dashboard', __name__, url_prefix='/user/dashboard')


@user_dashboard_bp.route('/')
@login_required
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil skor VARK berdasarkan user
    cursor.execute("""
        SELECT visual, auditory, reading, kinesthetic
        FROM scores_vark
        WHERE siswa_id = %s
        ORDER BY siswa_id DESC LIMIT 1
    """, (current_user.id,))

    vark_score = cursor.fetchone()

    # Ambil skor MLSQ berdasarkan user
    cursor.execute("""
        SELECT self_regulation, task_value, control_belief, goal_orientation, self_efficacy
        FROM scores_mlsq
        WHERE siswa_id = %s
        ORDER BY siswa_id DESC LIMIT 1
    """, (current_user.id,))
    mlsq_score = cursor.fetchone()

    # Ambil skor AMS
    cursor.execute("""
        SELECT intrinsic, extrinsic, amotivation
        FROM scores_ams
        WHERE siswa_id = %s
        ORDER BY siswa_id DESC LIMIT 1
    """, (current_user.id,))
    ams_score = cursor.fetchone()

    cursor.close()

    return render_template('user/user_dashboard.html',
                           vark_score=vark_score,
                           mlsq_score=mlsq_score,
                           ams_score=ams_score)
