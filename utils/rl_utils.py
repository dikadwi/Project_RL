from db import mysql
import MySQLdb.cursors


ACTION_CODES = [101, 105, 102, 103, 106]


# Ambil skor VARK, MLSQ, dan AMS dari tabel scores berdasarkan siswa_id
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

    return skor_vark, skor_mlsq, skor_ams


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


def init_state_actions(state):
    """Inisialisasi pasangan state-action di q_table jika belum ada."""
    cursor = mysql.connection.cursor()
    for code in ACTION_CODES:
        cursor.execute(
            """
            INSERT INTO q_table (state, action_code, q_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE q_value = q_value
            """,
            (state, code, 0.0),
        )
    mysql.connection.commit()
    cursor.close()


# Rekomendasi berdasarkan action code
def get_rekomendasi_dari_action(action_code, limit=5):
    """Ambil daftar rekomendasi berdasarkan ``action_code``.

    Mapping kode:
        101 -> reward
        102 -> produk (pembelian)
        103 -> hukuman
        105 -> misi
        106 -> pelatihan/konsultasi
    """
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    table_map = {
        101: "reward",
        102: "produk",
        103: "hukuman",
        105: "misi",
        106: "pelatihan",
    }

    table = table_map.get(action_code)
    if not table:
        cursor.close()
        return {}

    cursor.execute(f"SELECT * FROM {table} ORDER BY RAND() LIMIT %s", (limit,))
    items = cursor.fetchall()
    cursor.close()
    return {table: items}


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
