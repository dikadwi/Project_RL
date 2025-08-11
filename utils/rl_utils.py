import MySQLdb
import MySQLdb.cursors
from db import mysql

# Kode aksi yang dipakai di sistem
ACTION_CODES = [101, 105, 102, 103, 106]

# -------------------------------
# 1) Ambil skor dari DB
# -------------------------------


def ambil_skor_dari_db(siswa_id: int):
    """
    Ambil skor terbaru untuk VARK, MLSQ, dan AMS berdasarkan siswa_id.
    Disesuaikan dengan skema tabel:
      - scores_vark(visual, auditory, reading, kinesthetic)
      - scores_mlsq(self_regulation, task_value, control_belief, goal_orientation, self_efficacy)
      - scores_ams(intrinsic, extrinsic, amotivation)   <-- TANPA 'achievement'
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # VARK
    cur.execute(
        """
        SELECT visual, auditory, reading, kinesthetic
        FROM scores_vark
        WHERE siswa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (siswa_id,),
    )
    skor_vark = cur.fetchone()

    # MLSQ (5 dimensi -> kita rata-ratakan untuk level high/medium/low)
    cur.execute(
        """
        SELECT self_regulation, task_value, control_belief, goal_orientation, self_efficacy
        FROM scores_mlsq
        WHERE siswa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (siswa_id,),
    )
    skor_mlsq = cur.fetchone()

    # AMS (3 kolom saja)
    cur.execute(
        """
        SELECT intrinsic, extrinsic, amotivation
        FROM scores_ams
        WHERE siswa_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (siswa_id,),
    )
    skor_ams = cur.fetchone()

    cur.close()
    return skor_vark, skor_mlsq, skor_ams


# -------------------------------
# 2) Bangun state string
# -------------------------------
def build_state(skor_vark: dict, skor_mlsq: dict, skor_ams: dict, engagement: str):
    """
    Hasil state final: '<vark>-<mlsq-level>-<ams>-<engagement>'
    Contoh: 'visual-high-intrinsic-m3_f3_a3'
    """
    if not (skor_vark and skor_mlsq and skor_ams and engagement):
        return None

    # VARK: ambil dimensi skor tertinggi
    # visual|auditory|reading|kinesthetic
    vark = max(skor_vark, key=skor_vark.get)

    # MLSQ: rata-rata 5 dimensi -> level
    avg_mlsq = sum(skor_mlsq.values()) / len(skor_mlsq)
    if avg_mlsq >= 3.5:
        mlsq = "high"
    elif avg_mlsq >= 2.5:
        mlsq = "medium"
    else:
        mlsq = "low"

    # AMS: ambil skor tertinggi dari 3 kategori
    ams = max(skor_ams, key=skor_ams.get)  # intrinsic|extrinsic|amotivation

    return f"{vark}-{mlsq}-{ams}-{engagement}"


# -------------------------------
# 3) Ambil Top Actions dari Q-table
# -------------------------------
def get_top_actions(state_str: str, top_n: int = 3, limit: int | None = None):
    if limit is not None:
        top_n = limit

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        """
        SELECT action, q_value
        FROM q_table
        WHERE state = %s
        ORDER BY q_value DESC
        LIMIT %s
        """,
        (state_str, int(top_n)),
    )
    rows = cur.fetchall()
    cur.close()

    ACTION_MAP = {101: "Reward", 105: "Misi/Tantangan",
                  102: "Pembelian/Penukaran Poin", 103: "Hukuman/Denda", 106: "Konsultasi/Coaching"}
    out = []
    for r in rows:
        a = r["action"]
        code = int(a) if str(a).isdigit() else None
        label = ACTION_MAP.get(code, a)
        out.append({"action": label, "code": code, "q_value": r["q_value"]})
    return out


# -------------------------------
# 4) Inisialisasi state-action di q_table
# -------------------------------
def init_state_actions(state: str):
    """
    Insert pasangan (state, action) dengan q_value 0 jika belum ada.
    Kolom yang dipakai: (state, action, q_value).
    """
    cur = mysql.connection.cursor()
    for code in ACTION_CODES:
        cur.execute(
            """
            INSERT INTO q_table (state, action, q_value)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE q_value = q_value
            """,
            (state, code, 0.0),
        )
    mysql.connection.commit()
    cur.close()


# -------------------------------
# 5) Rekomendasi item berdasarkan action
# -------------------------------
def get_rekomendasi_dari_action(action_code: int, limit: int = 5):
    """
    101 -> reward
    102 -> produk
    103 -> hukuman
    105 -> misi
    106 -> pelatihan
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    table_map = {
        101: "reward",
        102: "produk",
        103: "hukuman",
        105: "misi",
        106: "pelatihan",
    }
    table = table_map.get(action_code)
    if not table:
        cur.close()
        return {}

    cur.execute(
        f"SELECT * FROM {table} ORDER BY RAND() LIMIT %s", (int(limit),))
    items = cur.fetchall()
    cur.close()
    return {table: items}


# -------------------------------
# 6) Update Q-value (Q-learning)
# -------------------------------
def update_q_value(state: str, action_code: int, reward: float, alpha: float = 0.1, gamma: float = 0.9):
    """
    Update Q(s, a) = Q(s, a) + alpha * (reward + gamma * max_a' Q(s, a') - Q(s, a))
    Menggunakan kolom 'action' pada q_table.
    """
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Q lama
    cur.execute(
        "SELECT q_value FROM q_table WHERE state = %s AND action = %s",
        (state, action_code),
    )
    row = cur.fetchone()
    current_q = row["q_value"] if row else 0.0

    # Max Q untuk state yang sama
    cur.execute(
        "SELECT MAX(q_value) AS max_q FROM q_table WHERE state = %s",
        (state,),
    )
    max_q_row = cur.fetchone()
    max_q = max_q_row["max_q"] if max_q_row and max_q_row["max_q"] is not None else 0.0

    # Rumus Q-learning
    new_q = current_q + alpha * (reward + gamma * max_q - current_q)

    # Simpan
    cur.execute(
        "UPDATE q_table SET q_value = %s WHERE state = %s AND action = %s",
        (new_q, state, action_code),
    )
    mysql.connection.commit()
    cur.close()
    return new_q


# -------------------------------
# 7) Log rekomendasi
# -------------------------------
def simpan_log_rekomendasi(siswa_id: int, state: str, best_action: str):
    cur = mysql.connection.cursor()
    cur.execute(
        """
        INSERT INTO log_rekomendasi (siswa_id, state, best_action)
        VALUES (%s, %s, %s)
        """,
        (siswa_id, state, best_action),
    )
    mysql.connection.commit()
    cur.close()


# -------------------------------
# 8) Generator daftar state (untuk seeding)
# -------------------------------
def generate_all_states():
    vark_opts = ["visual", "auditory", "reading", "kinesthetic"]
    mlsq_opts = ["high", "medium", "low"]
    # AMS disesuaikan dengan DB: TIGA opsi saja
    ams_opts = ["intrinsic", "extrinsic", "amotivation"]
    eng_opts = ["m1_f1_a1", "m2_f2_a2", "m3_f3_a3"]

    return [
        f"{v}-{m}-{a}-{e}"
        for v in vark_opts
        for m in mlsq_opts
        for a in ams_opts
        for e in eng_opts
    ]
