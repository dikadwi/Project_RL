from flask import redirect, url_for
from db import mysql
from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == 'admin':
        return render_template("admin/dashboard_admin.html")
    elif current_user.role == 'user':
        return render_template("dosen/dashboard_user.html")
    else:
        return "Role tidak dikenali", 403


@dashboard_bp.route("/logs")
@login_required
def logs():
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM activity_log WHERE user_id = %s ORDER BY start_time DESC", (current_user.id,))
    logs = cursor.fetchall()
    cursor.close()
    return render_template("log_user.html", logs=logs)
