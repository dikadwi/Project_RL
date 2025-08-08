from flask import Blueprint, render_template
from flask_login import login_required, current_user

profil_bp = Blueprint('profil', __name__)


@profil_bp.route('/profil')
@login_required
def index():
    return render_template('profil.html', user=current_user)
