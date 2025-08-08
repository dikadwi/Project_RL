from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from db import mysql
import os
from werkzeug.utils import secure_filename
import pandas as pd
import MySQLdb.cursors

admin_produk_bp = Blueprint(
    'admin_produk', __name__, url_prefix='/admin/produk')

ALLOWED_EXTENSIONS = {"csv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_next_produk_id():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        "SELECT MAX(CAST(SUBSTRING(id_produk, 2) AS UNSIGNED)) AS max_id FROM produk")
    row = cur.fetchone()
    cur.close()
    last_num = row["max_id"] if row and row["max_id"] is not None else 0
    return f"P{last_num+1:03d}"


@admin_produk_bp.route("/", methods=["GET"])
@login_required
def index():
    if current_user.role != "admin":
        return "Unauthorized", 403

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM produk ORDER BY CAST(SUBSTRING(id_produk,2) AS UNSIGNED)")
    produk_data = cursor.fetchall()
    cursor.close()

    next_id = get_next_produk_id()
    vark_opts = ["V", "A", "R", "K"]
    mlsq_opts = ["low", "medium", "high"]
    ams_opts = ["intrinsic", "extrinsic", "amotivation"]
    engage_opts = ["m1_f1_a1", "m2_f2_a2", "m3_f3_a3"]

    return render_template("admin/admin_produk_list.html",
                           produk=produk_data,
                           next_id=next_id,
                           vark_opts=vark_opts,
                           mlsq_opts=mlsq_opts,
                           ams_opts=ams_opts,
                           engage_opts=engage_opts)


@admin_produk_bp.route("/save", methods=["POST"])
@login_required
def save_produk():
    if current_user.role != "admin":
        return "Unauthorized", 403

    _id = request.form.get("id_produk") or get_next_produk_id()
    judul = request.form.get("judul")
    deskripsi = request.form.get("deskripsi")
    kategori = request.form.get("kategori")
    poin = request.form.get("poin") or 0
    kode_action = request.form.get("kode_action") or 102

    target_state = request.form.get("target_state")
    if not target_state:
        ts_vark = request.form.get("ts_vark")
        ts_mlsq = request.form.get("ts_mlsq")
        ts_ams = request.form.get("ts_ams")
        ts_eng = request.form.get("ts_eng")
        target_state = f"{ts_vark} + {ts_mlsq} + {ts_ams} + {ts_eng}"

    cursor = mysql.connection.cursor()
    sql = """
        INSERT INTO produk (id_produk, judul, deskripsi, kategori, poin, target_state, kode_action)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            judul=%s, deskripsi=%s, kategori=%s, poin=%s, target_state=%s, kode_action=%s
    """
    params = (_id, judul, deskripsi, kategori, poin, target_state, kode_action,
              judul, deskripsi, kategori, poin, target_state, kode_action)
    cursor.execute(sql, params)
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('admin_produk.index'))


@admin_produk_bp.route("/delete/<string:id_produk>", methods=["POST"])
@login_required
def delete_produk(id_produk):
    if current_user.role != "admin":
        return "Unauthorized", 403
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM produk WHERE id_produk = %s", (id_produk,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('admin_produk.index'))


@admin_produk_bp.route("/upload", methods=["POST"])
@login_required
def upload_csv_produk():
    if current_user.role != "admin":
        return "Unauthorized", 403

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("⚠️ Pilih file CSV terlebih dahulu.")
        return redirect(url_for("admin_produk.index"))

    if not allowed_file(file.filename):
        flash("❌ Hanya file CSV yang diizinkan.")
        return redirect(url_for("admin_produk.index"))

    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(upload_path)

    try:
        df = pd.read_csv(upload_path)
        required_cols = {"id_produk", "judul", "deskripsi",
                         "kategori", "poin", "target_state", "kode_action"}
        if not required_cols.issubset(df.columns):
            flash(f"❌ CSV harus punya kolom: {required_cols}")
            return redirect(url_for("admin_produk.index"))

        df = df.fillna("")
        rows = list(df[["id_produk", "judul", "deskripsi", "kategori", "poin", "target_state", "kode_action"]]
                    .itertuples(index=False, name=None))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql = """
            INSERT INTO produk (id_produk, judul, deskripsi, kategori, poin, target_state, kode_action)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                judul=VALUES(judul),
                deskripsi=VALUES(deskripsi),
                kategori=VALUES(kategori),
                poin=VALUES(poin),
                target_state=VALUES(target_state),
                kode_action=VALUES(kode_action)
        """
        cursor.executemany(sql, rows)
        mysql.connection.commit()
        cursor.close()

        flash(f"✅ Berhasil impor {len(rows)} produk dari CSV.")
    except Exception as e:
        flash(f"❌ Gagal impor CSV: {e}")
    finally:
        if os.path.exists(upload_path):
            os.remove(upload_path)

    return redirect(url_for("admin_produk.index"))
