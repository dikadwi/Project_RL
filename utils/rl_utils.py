from db import mysql
import MySQLdb.cursors


# Hitung engagement berdasarkan frekuensi dan durasi interaksi
def hitung_engagement(siswa_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        """
        SELECT COUNT(*) AS freq, COALESCE(SUM(duration_seconds), 0) AS total_dur
        FROM activity_log
        WHERE user_id = %s AND start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """,
        (siswa_id,),
    )
    data = cursor.fetchone() or {"freq": 0, "total_dur": 0}
    cursor.close()

    freq = data["freq"]
    dur = data["total_dur"]

    if freq >= 10 or dur >= 3600:
        return "m3_f3_a3"
    if freq >= 5 or dur >= 1800:
        return "m2_f2_a2"
    return "m1_f1_a1"


# Ambil skor VARK, MLSQ, AMS dan engagement dari tabel scores berdasarkan siswa_id
def ambil_skor_dari_db(siswa_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        """
        SELECT visual, auditory, reading, kinesthetic
        FROM scores_vark
        WHERE siswa_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (siswa_id,),
    )
    skor_vark = cursor.fetchone()

    cursor.execute(
        """
        SELECT self_regulation, task_value, control_belief, goal_orientation, self_efficacy
        FROM scores_mlsq
        WHERE siswa_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (siswa_id,),
    )
    skor_mlsq = cursor.fetchone()

    cursor.execute(
        """
        SELECT intrinsic, extrinsic, amotivation, achievement
        FROM scores_ams
        WHERE siswa_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (siswa_id,),
    )
    skor_ams = cursor.fetchone()

    cursor.close()

    engagement = hitung_engagement(siswa_id)
    return skor_vark, skor_mlsq, skor_ams, engagement


# Buat state string dari skor-skor
def build_state(skor_vark, skor_mlsq, skor_ams, engagement):
    if not (skor_vark and skor_mlsq and skor_ams and engagement):
        return None  # Tangani jika skor belum tersedia

    vark = max(skor_vark, key=skor_vark.get)

    avg_mlsq = sum(skor_mlsq.values()) / len(skor_mlsq)
    if avg_mlsq >= 3.5:
        mlsq = "high"
    elif avg_mlsq >= 2.5:
        mlsq = "medium"
    else:
        mlsq = "low"

    ams = max(skor_ams, key=skor_ams.get)

    return f"{vark}-{mlsq}-{ams}-{engagement}"


# Ambil best action dari Q-table
def get_top_actions(skor_vark, skor_mlsq, skor_ams, engagement, limit=3):
    """Ambil daftar action_code dengan Q-value tertinggi untuk state tertentu."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    state_str = build_state(skor_vark, skor_mlsq, skor_ams, engagement)

    cursor.execute(
        """
        SELECT action_code, q_value
        FROM q_table
        WHERE state = %s
        ORDER BY q_value DESC
        LIMIT %s
        """,
        (state_str, limit),
    )
    rows = cursor.fetchall()
    cursor.close()

    return state_str, rows  # rows berisi action_code dan q_value


# Rekomendasi misi & reward berdasarkan action code
def get_rekomendasi_dari_action(state, action_code, misi_limit=3, reward_limit=2):
    """Kembalikan rekomendasi berdasarkan state dan action_code.

    Action code:
        101: reward
        105: misi
    Kode lain belum memiliki rekomendasi spesifik sehingga mengembalikan list kosong.
    """
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if not state:
        return [], []

    try:
        vark, mlsq, ams, *_ = state.split("-")
    except ValueError:
        return [], []

    misi, reward = [], []
    if action_code == 105:  # misi
        cursor.execute(
            "SELECT * FROM misi WHERE vark = %s AND mlsq = %s AND ams = %s ORDER BY RAND() LIMIT %s",
            (vark, mlsq, ams, misi_limit),
        )
        misi = cursor.fetchall()
    elif action_code == 101:  # reward
        cursor.execute(
            "SELECT * FROM reward WHERE vark_bonus = %s AND ams_target = %s ORDER BY poin_dibutuhkan ASC LIMIT %s",
            (vark, ams, reward_limit),
        )
        reward = cursor.fetchall()

    cursor.close()
    return misi, reward


def update_q_value(state, action_code, reward, alpha=0.1, gamma=0.9):
    """Perbarui nilai Q pada tabel berdasarkan feedback yang diterima."""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil Q-value saat ini
    cursor.execute(
        "SELECT q_value FROM q_table WHERE state = %s AND action_code = %s",
        (state, action_code),
    )
    row = cursor.fetchone()
    current_q = row["q_value"] if row else 0.0

    # Ambil Q-value maksimum untuk state yang sama
    cursor.execute(
        "SELECT MAX(q_value) AS max_q FROM q_table WHERE state = %s",
        (state,),
    )
    max_q_row = cursor.fetchone()
    max_q = max_q_row["max_q"] if max_q_row and max_q_row["max_q"] is not None else 0.0

    # Rumus Q-learning
    new_q = current_q + alpha * (reward + gamma * max_q - current_q)

    cursor.execute(
        "UPDATE q_table SET q_value = %s WHERE state = %s AND action_code = %s",
        (new_q, state, action_code),
    )
    mysql.connection.commit()
    cursor.close()
    return new_q


# Simpan log rekomendasi
def simpan_log_rekomendasi(siswa_id, state, action):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO log_rekomendasi (siswa_id, state, best_action) 
        VALUES (%s, %s, %s)
    """, (siswa_id, state, action))
    mysql.connection.commit()
    cursor.close()


# Hasilkan daftar semua state unik
def generate_all_states():
    vark_opts = ["visual", "auditory", "reading", "kinesthetic"]
    mlsq_opts = ["high", "medium", "low"]
    ams_opts = ["intrinsic", "extrinsic", "amotivation", "achievement"]
    eng_opts = ["m1_f1_a1", "m2_f2_a2", "m3_f3_a3"]
    return [
        f"{v}-{m}-{a}-{e}"
        for v in vark_opts
        for m in mlsq_opts
        for a in ams_opts
        for e in eng_opts
    ]
