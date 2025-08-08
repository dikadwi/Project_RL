from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from utils.rl_utils import (
    ambil_skor_dari_db,
    get_top_actions,
    get_rekomendasi_dari_action,
    simpan_log_rekomendasi,
    update_q_value,
)

rekomendasi_bp = Blueprint("rekomendasi", __name__, url_prefix='/rl')


@rekomendasi_bp.route("/rekomendasi")
@login_required
def rekomendasi():
    siswa_id = current_user.id

    # Ambil skor termasuk engagement
    skor_vark, skor_mlsq, skor_ams, engagement = ambil_skor_dari_db(siswa_id)

    # Bangun state & top actions
    state_str, top_actions = get_top_actions(
        skor_vark, skor_mlsq, skor_ams, engagement, limit=3)

    action_map = {
        101: "reward",
        105: "misi",
        102: "pembelian",
        103: "hukuman",
        106: "konsultasi",
    }

    for a in top_actions:
        a["action_name"] = action_map.get(a["action_code"], str(a["action_code"]))

    best_action = top_actions[0]["action_code"] if top_actions else None
    rekomendasi = get_rekomendasi_dari_action(best_action) if best_action else {}

    # Simpan log
    if best_action is not None:
        simpan_log_rekomendasi(siswa_id, state_str, best_action)

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
