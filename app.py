
from flask import Flask
from flask_login import LoginManager
from flask import redirect, url_for
from db import mysql
from flask_login import LoginManager
from MySQLdb.cursors import DictCursor
import MySQLdb.cursors
import os
# Models
from models.user import load_user
# Routes
from routes.admin.admin_siswa import admin_siswa_bp
from routes.admin.admin_reward import admin_reward_bp
from routes.admin.admin_misi import admin_misi_bp
from routes.admin.admin_produk import admin_produk_bp
from routes.admin.admin_hukuman import admin_hukuman_bp
from routes.admin.admin_pelatihan import admin_pelatihan_bp
from routes.admin.admin_Q_vark import admin_q_vark
from routes.admin.admin_Q_ams import admin_q_ams
from routes.admin.admin_Q_mlsq import admin_q_mlsq
# Kuisioner
from routes.kuisioner.kuisioner_vark import kuisioner_vark_bp
from routes.kuisioner.kuisioner_mlsq import kuisioner_mlsq_bp
from routes.kuisioner.kuisioner_ams import kuisioner_ams_bp
# rl
from routes.rl.rekomendasi import rekomendasi_bp
# from routes.auth import User
from routes.profil import profil_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.rl_latest import rl_bp
from routes.user.user_dashboard import user_dashboard_bp


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config.from_pyfile('config.py')


# 🔌 Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pointmarket_rl'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# 🔹 Folder penyimpanan sementara file upload
app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

mysql.init_app(app)

# 🔐 Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


# 📌 Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(rl_bp)
app.register_blueprint(admin_misi_bp)
app.register_blueprint(admin_reward_bp)
app.register_blueprint(admin_produk_bp)
app.register_blueprint(admin_hukuman_bp)
app.register_blueprint(admin_pelatihan_bp)
app.register_blueprint(admin_siswa_bp)
app.register_blueprint(user_dashboard_bp)
app.register_blueprint(admin_q_vark)
app.register_blueprint(admin_q_ams)
app.register_blueprint(admin_q_mlsq)
app.register_blueprint(profil_bp)
app.register_blueprint(kuisioner_vark_bp)
app.register_blueprint(kuisioner_mlsq_bp)
app.register_blueprint(kuisioner_ams_bp)
app.register_blueprint(rekomendasi_bp)


# 🧑 User Loader
login_manager.user_loader(load_user)


@login_manager.user_loader
def user_loader(user_id):
    return load_user(user_id)


# @login_manager.user_loader
# def load_user(user_id):
#     cursor = mysql.connection.cursor()
#     cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
#     user = cursor.fetchone()
#     return User(user) if user else None


@app.route("/")
def root():
    return redirect(url_for("auth.login"))


if __name__ == '__main__':
    app.run(debug=True)
