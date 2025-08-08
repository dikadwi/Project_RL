from db import mysql
import MySQLdb.cursors


# Ambil skor VARK, MLSQ, AMS dari tabel scores berdasarkan siswa_id
def ambil_skor_dari_db(siswa_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT visual, auditory, reading, kinesthetic 
        FROM scores_vark 
        WHERE siswa_id = %s 
        ORDER BY created_at DESC LIMIT 1
    """, (siswa_id,))
    skor_vark = cursor.fetchone()

    cursor.execute("""
        SELECT self_regulation, task_value, control_belief, goal_orientation, self_efficacy 
        FROM scores_mlsq 
        WHERE siswa_id = %s 
        ORDER BY created_at DESC LIMIT 1
    """, (siswa_id,))
    skor_mlsq = cursor.fetchone()

    cursor.execute("""
        SELECT intrinsic, extrinsic, amotivation 
        FROM scores_ams 
        WHERE siswa_id = %s 
        ORDER BY created_at DESC LIMIT 1
    """, (siswa_id,))
    skor_ams = cursor.fetchone()

    cursor.close()
    return skor_vark, skor_mlsq, skor_ams


# Buat state string dari skor-skor
def build_state(skor_vark, skor_mlsq, skor_ams):
    if not (skor_vark and skor_mlsq and skor_ams):
        return None  # Tangani jika skor belum tersedia

    vark = max(skor_vark, key=skor_vark.get)
    mlsq = max(skor_mlsq, key=skor_mlsq.get)
    ams = max(skor_ams, key=skor_ams.get)
    return f"{vark}-{mlsq}-{ams}"


# Ambil best action dari Q-table
def get_top_actions(skor_vark, skor_mlsq, skor_ams, limit=3):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    state_str = build_state(skor_vark, skor_mlsq, skor_ams)

    cursor.execute(
        "SELECT * FROM q_table WHERE state = %s ORDER BY q_value DESC LIMIT %s", (state_str, limit))
    rows = cursor.fetchall()
    cursor.close()

    return state_str, rows  # rows = list of actions


# Rekomendasi misi & reward berdasarkan action
def get_rekomendasi_dari_action(action, misi_limit=3, reward_limit=2):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if not action:
        return [], []

    try:
        vark, mlsq, ams = action.split("-")
    except ValueError:
        return [], []

    cursor.execute(
        "SELECT * FROM misi WHERE vark = %s AND mlsq = %s AND ams = %s ORDER BY RAND() LIMIT %s",
        (vark, mlsq, ams, misi_limit)
    )
    misi = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM reward WHERE vark_bonus = %s AND ams_target = %s ORDER BY poin_dibutuhkan ASC LIMIT %s",
        (vark, ams, reward_limit)
    )
    reward = cursor.fetchall()

    cursor.close()
    return misi, reward


# Simpan log rekomendasi
def simpan_log_rekomendasi(siswa_id, state, action):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO log_rekomendasi (siswa_id, state, best_action) 
        VALUES (%s, %s, %s)
    """, (siswa_id, state, action))
    mysql.connection.commit()
    cursor.close()
