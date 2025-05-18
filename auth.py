"""
██████╗ ███████╗███╗   ██╗████████╗ ██████╗  ██████╗  █████╗ ██████╗ ██████╗ 
██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗
██║  ██║█████╗  ██╔██╗ ██║   ██║   ██║   ██║██║  ███╗███████║██████╔╝██║  ██║
██║  ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
██████╔╝███████╗██║ ╚████║   ██║   ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
    copyright  2025 DentoGuard_Ebwer                                                                          
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, template_folder='templates')
_users = {}

class User(UserMixin):
    def __init__(self, username, password):
        self.id = username
        self.password_hash = generate_password_hash(password)

    @staticmethod
    def get(user_id):
        return _users.get(user_id)

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        if u in _users:
            flash("Username already exists", "error")
        else:
            _users[u] = User(u, p)
            flash("Signup successful—please log in", "success")
            return redirect(url_for('auth.login'))
    return render_template('signup.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.get(u)
        if user and check_password_hash(user.password_hash, p):
            login_user(user)
            return redirect(url_for('dataset.upload'))
        flash("Invalid credentials", "error")
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out", "info")
    return redirect(url_for('auth.login'))
