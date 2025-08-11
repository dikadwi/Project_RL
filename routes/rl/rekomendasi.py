from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from utils.rl_utils import (
    ambil_skor_dari_db,
    build_state,                 # ⬅️ pastikan di-import
    get_top_actions,
    get_rekomendasi_dari_action,
    init_state_actions,
    simpan_log_rekomendasi,
    update_q_value,
)

rekomendasi_bp = Blueprint("rekomendasi", __name__, url_prefix="/rl")


@rekomendasi_bp.route("/rekomendasi")
@login_required
def rekomendasi():
    siswa_id = current_user.id

    # 1) Ambil skor & engagement
    skor_vark, skor_mlsq, skor_ams = ambil_skor_dari_db(siswa_id)

    # Kalau skor belum ada/lengkap, tampilkan pesan ramah
    if not (skor_vark and skor_mlsq and skor_ams):
        return render_template(
            "rl/rekomendasi.html",
            error="Skor kuisioner belum lengkap. Mohon lengkapi VARK, MLSQ, dan AMS.",
            state=None,
            top_actions=[],
            rekomendasi={},
            skor_vark=skor_vark,
            skor_mlsq=skor_mlsq,
            skor_ams=skor_ams,
            engagement=None,
        )

    # Ambil engagement dari user; fallback aman bila method tidak ada/None
    try:
        engagement = current_user.get_engagement()
    except Exception:
        engagement = None
    if not engagement:
        # fallback default aman (silakan sesuaikan)
        engagement = "m2_f2_a2"

    # 2) Bangun state
    state_str = build_state(skor_vark, skor_mlsq, skor_ams, engagement)
    if not state_str:
        return render_template(
            "rl/rekomendasi.html",
            error="Gagal membangun state. Periksa skor/engagement.",
            state=None,
            top_actions=[],
            rekomendasi={},
            skor_vark=skor_vark,
            skor_mlsq=skor_mlsq,
            skor_ams=skor_ams,
            engagement=engagement,
        )

    # 3) Ambil Top-N actions dari q_table
    #    (utils sudah mendukung alias limit=)
    top_actions = get_top_actions(siswa_id, state_str, limit=3)

    # Jika belum ada pasangan state-action, seed dulu lalu tampilkan pesan
    if not top_actions:
        init_state_actions(state_str)
        # opsional: bisa fetch ulang di sini jika ingin langsung muncul
        # top_actions = get_top_actions(siswa_id, state_str, limit=3)
        return render_template(
            "rl/rekomendasi.html",
            state=state_str,
            top_actions=[],
            rekomendasi={},
            skor_vark=skor_vark,
            skor_mlsq=skor_mlsq,
            skor_ams=skor_ams,
            engagement=engagement,
            message="State baru diinisialisasi. Silakan refresh untuk melihat rekomendasi.",
        )

    # 4) Lengkapi label action untuk tampilan
    action_map = {
        101: "reward",
        105: "misi",
        102: "produk",       # selaras dengan table_map di utils
        103: "hukuman",
        106: "pelatihan",
    }

    for a in top_actions:
        # utils mengembalikan key: "code" (int|None), "action" (label ramah), "q_value"
        code = a.get("code")
        a["action_code"] = code
        a["action_name"] = action_map.get(
            code, str(code) if code is not None else a.get("action"))

    # 5) Rekomendasi item berdasarkan best action
    best_action_code = top_actions[0]["action_code"]
    rekomendasi = get_rekomendasi_dari_action(best_action_code, limit=5)

    # 6) Log
    simpan_log_rekomendasi(siswa_id, state_str, str(best_action_code))

    # 7) Render
    return render_template(
        "rl/rekomendasi.html",
        state=state_str,
        top_actions=top_actions,
        rekomendasi=rekomendasi,
        skor_vark=skor_vark,
        skor_mlsq=skor_mlsq,
        skor_ams=skor_ams,
        engagement=engagement,
    )


@rekomendasi_bp.route("/feedback", methods=["POST"])
@login_required
def feedback():
    state = request.form.get("state")
    action_code = int(request.form.get("action_code"))
    reward = float(request.form.get("reward"))
    alpha = float(request.form.get("alpha", 0.1))
    gamma = float(request.form.get("gamma", 0.9))
    update_q_value(state, action_code, reward, alpha, gamma)
    return {"status": "updated"}
