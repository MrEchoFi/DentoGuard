"""
██████╗ ███████╗███╗   ██╗████████╗ ██████╗  ██████╗  █████╗ ██████╗ ██████╗ 
██╔══██╗██╔════╝████╗  ██║╚══██╔══╝██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗
██║  ██║█████╗  ██╔██╗ ██║   ██║   ██║   ██║██║  ███╗███████║██████╔╝██║  ██║
██║  ██║██╔══╝  ██║╚██╗██║   ██║   ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
██████╔╝███████╗██║ ╚████║   ██║   ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
        copyright  2025 DentoGuard_Ebwer                                                                 
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (LoginManager, UserMixin,
                         login_user, login_required,
                         logout_user, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import cv2, numpy as np


app = Flask(__name__)
app.secret_key = 'tsecret777'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXT = {'png','jpg','jpeg','gif'}


login_manager = LoginManager(app)
login_manager.login_view = 'login'


_users = {}

class User(UserMixin):
    def __init__(self, username, pw_hash):
        self.id = username
        self.password_hash = pw_hash

    @classmethod
    def create(cls, username, password):
        user = cls(username, generate_password_hash(password))
        _users[username] = user
        return user

    @staticmethod
    def get(username):
        return _users.get(username)

@login_manager.user_loader
def load_user(username):
    return User.get(username)


def load_infection_types():
    d = {}
    with open('infection_types.txt') as f:
        for line in f:
            if ':' in line:
                k, v = line.strip().split(':', 1)
                d[k.strip()] = v.strip()
    return d

infection_data = load_infection_types()


def allowed_file(fn):
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXT

"""def is_tooth_image(path):
    img = cv2.imread(path)
    if img is None: return False
    h,w = img.shape[:2]; total = h*w

    # Relaxed HSV mask for tooth‑like pixels
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0,10,100]), np.array([100,80,255]))
    color_ratio = cv2.countNonZero(mask)/total

    # Edge density
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray,50,150)
    edge_ratio = cv2.countNonZero(edges)/edges.size

    # Bright region shape
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts: return False
    c = max(cnts, key=cv2.contourArea)
    area_ratio = cv2.contourArea(c)/total

    return (color_ratio > 0.05 and edge_ratio > 0.01 and area_ratio > 0.02) """

def is_tooth_image(image_path):
  
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        return False
    h, w = img_cv.shape[:2]

    # 1) Grid sampling
    step_x, step_y = max(1, w//20), max(1, h//20)
    white = total = 0
    for x in range(0, w, step_x):
        for y in range(0, h, step_y):
            b, g, r = img_cv[y, x]
            intensity = (int(r) + int(g) + int(b)) / 3
            saturation = max(int(r), int(g), int(b)) - min(int(r), int(g), int(b))
            total += 1
            if intensity > 200 and saturation < 30:
                white += 1
    white_ratio = (white / total) if total else 0

    
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    x0, y0, w0, h0 = cv2.boundingRect(mask)
    box_area_ratio = ((w0 * h0) / (w * h)) if (w * h) else 0

   
    edges = cv2.Canny(gray, 100, 200)
    edge_ratio = np.count_nonzero(edges) / edges.size

  
    white_cond = (0.01 < white_ratio < 0.8)
    box_cond   = (box_area_ratio > 0.015)
    edge_cond  = (edge_ratio < 0.15)

    return sum([white_cond, box_cond, edge_cond]) >= 2

def detect_infection(path):
    img = Image.open(path).convert('L')
    w,h = img.size; pix = img.load(); total = w*h
    dark = sum(1 for x in range(w) for y in range(h) if pix[x,y]<128)
    damage = round(dark/total*100,2)

    """This is the Secondary Error Handling for the dataset which can predict infection and u can say why we add this
    because we build this dataset by our own in short time and human can mistake that is why when dataset can not predict correctly & facing conflict then this Error handling function will be used"""

    if damage < 10: inf='healthy'
    elif damage < 30: inf='cavities'
    elif damage < 50: inf='enamel erosion'
    elif damage < 70: inf='gum infection'
    elif damage < 90: inf='abscess'
    else: inf='periodontal disease'

    return inf, damage, infection_data.get(inf, 'No recommendation available.')


@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        u = request.form['username']
        p = request.form['password']
        if u in _users:
            flash('Username already exists','error')
        else:
            User.create(u,p)
            flash('Signup successful! Please login.','success')
            return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form['username']
        p = request.form['password']
        user = User.get(u)
        if user and check_password_hash(user.password_hash, p):
            login_user(user)
            return redirect(url_for('upload'))
        flash('Invalid credentials','error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out','info')
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method=='POST':
        f = request.files.get('file')
        if not f or not allowed_file(f.filename):
            flash('Please select a valid image','error')
            return redirect(url_for('upload'))
        fn = secure_filename(f.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        p = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(p)

        if not is_tooth_image(p):
            os.remove(p)
            flash("That doesn't look like a tooth","error")
            return redirect(url_for('upload'))

        inf, dmg, rec = detect_infection(p)
        return render_template('result.html',
                               infection=inf,
                               damage=dmg,
                               recommendation=rec,
                               filename=fn)
    return render_template('upload.html')

@app.route('/')
def index():
    return redirect(url_for('upload') if current_user.is_authenticated else url_for('login'))

if __name__=='__main__':
    app.run(debug=True)
