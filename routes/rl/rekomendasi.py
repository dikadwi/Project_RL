from flask import Blueprint, render_template
from flask_login import login_required, current_user
from utils.rl_utils import (
    ambil_skor_dari_db,
    get_top_actions,
    get_rekomendasi_dari_action,
    simpan_log_rekomendasi,
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

    # Ambil rekomendasi dari action pertama (paling besar Q-value)
    rekom_misi, rekom_reward = get_rekomendasi_dari_action(
        top_actions[0]['action'], misi_limit=5, reward_limit=5)

    # Simpan log
    simpan_log_rekomendasi(siswa_id, state_str, top_actions[0]['action'])

    return render_template(
        "rl/rekomendasi.html",
        state=state_str,
        top_actions=top_actions,
        rekom_misi=rekom_misi,
        rekom_reward=rekom_reward,
        skor_vark=skor_vark,
        skor_mlsq=skor_mlsq,
        skor_ams=skor_ams,
        engagement=engagement
    )
