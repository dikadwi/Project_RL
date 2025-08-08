from activity_log import log_activity
from data.misi_data import misi_list
from data.reward_data import reward_list
import random
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user
from datetime import datetime
from db import mysql

rl_bp = Blueprint("rl", __name__, url_prefix="/rl")

# Definisi keys
vark_keys = ["visual", "auditory", "reading", "kinesthetic"]
mlsq_keys = ["self-regulation", "task-value",
             "control-belief", "goal-orientation", "self-efficacy"]
ams_keys = ["intrinsic", "extrinsic", "amotivation"]
actions = [(v, m, a) for v in vark_keys for m in mlsq_keys for a in ams_keys]

# RL dummy training untuk Q-table
Q = {action: 0.0 for action in actions}
alpha, gamma, epsilon, episodes = 0.1, 0.9, 0.2, 500


def compute_reward(action, skor_vark, skor_mlsq, skor_ams):
    v, m, a = action
    return skor_vark[v]*0.4 + skor_mlsq[m]*0.4 + skor_ams[a]*0.2


for _ in range(episodes):
    dummy_vark = {k: random.uniform(0, 1) for k in vark_keys}
    dummy_mlsq = {k: random.uniform(0, 1) for k in mlsq_keys}
    dummy_ams = {k: random.uniform(0, 1) for k in ams_keys}
    action = random.choice(actions) if random.uniform(
        0, 1) < epsilon else max(Q, key=Q.get)
    reward = compute_reward(action, dummy_vark, dummy_mlsq, dummy_ams)
    Q[action] += alpha * (reward + gamma * max(Q.values()) - Q[action])


@rl_bp.route("/kuisioner", methods=["GET", "POST"])
@login_required
def kuisioner():
    if request.method == "POST":
        start_time = datetime.strptime(
            request.form['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        skor_vark = {k: float(request.form[k]) / 10 for k in vark_keys}
        skor_mlsq = {k: float(request.form[k]) / 10 for k in mlsq_keys}
        skor_ams = {k: float(request.form[k]) / 10 for k in ams_keys}

        # Simpan ke DB
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO kuisioner (user_id, vark_scores, mlsq_scores, ams_scores, duration_seconds)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            current_user.id,
            str(skor_vark), str(skor_mlsq), str(skor_ams),
            int(duration)
        ))
        mysql.connection.commit()
        cursor.close()

        # 🔍 Tambahkan logging aktivitas kuisioner di sini:
        log_activity(
            current_user.id,
            "kuisioner",
            "Mengisi kuisioner VARK + MLSQ + AMS",
            start_time,
            end_time
        )

        # Simpan skor ke session
        session['skor_vark'] = skor_vark
        session['skor_mlsq'] = skor_mlsq
        session['skor_ams'] = skor_ams

        return redirect(url_for("rl.misi"))

    # return render_template("user/kuisioner_....html",
    return render_template("kuisioner.html",
                           vark_keys=vark_keys,
                           mlsq_keys=mlsq_keys,
                           ams_keys=ams_keys,
                           start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@rl_bp.route("/misi")
@login_required
def misi():
    if not all(k in session for k in ["skor_vark", "skor_mlsq", "skor_ams"]):
        return redirect(url_for("rl.kuisioner"))

    skor_vark = session['skor_vark']
    skor_mlsq = session['skor_mlsq']
    skor_ams = session['skor_ams']

    q_values = [(a, compute_reward(a, skor_vark, skor_mlsq, skor_ams))
                for a in actions]
    top_3 = sorted(q_values, key=lambda x: x[1], reverse=True)[:3]

    result = []
    for (v, m, a), qval in top_3:
        misi_cocok = [misi for misi in misi_list if misi['vark']
                      == v and misi['mlsq'] == m and misi['ams'] == a][:5]
        reward_cocok = [r for r in reward_list if r['vark_bonus']
                        == v and r['ams_target'] == a][:5]
        result.append({
            "action": f"{v}-{m}-{a}",
            "Q_value": round(qval, 3),
            "misi": misi_cocok,
            "reward": reward_cocok
        })

    return render_template("misi_list.html", result=result)
