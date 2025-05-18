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
from flask_login import login_required
from werkzeug.utils import secure_filename
from PIL import Image
import os, cv2, numpy as np

bp = Blueprint('dataset', __name__, template_folder='templates')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

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
    return '.' in fn and fn.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def is_tooth_image(path):
    img = cv2.imread(path)
    if img is None:
        return False
    h, w = img.shape[:2]; total=h*w
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([0,0,200]), np.array([50,80,255]))
    color_ratio = cv2.countNonZero(mask)/total
    edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),100,200)
    edge_ratio = cv2.countNonZero(edges)/edges.size
    cnts,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return False
    c = max(cnts, key=cv2.contourArea)
    area_ratio = cv2.contourArea(c)/total
    x,y,w0,h0 = cv2.boundingRect(c)
    aspect = h0/(w0 or 1)
    return (color_ratio>=0.15 and 0.02<=edge_ratio<=0.30
            and area_ratio>=0.05 and 0.5<=aspect<=2.0)

def detect_infection(path):
    img = Image.open(path).convert('L')
    w,h = img.size; pix=img.load()
    total=w*h
    dark = sum(1 for x in range(w) for y in range(h) if pix[x,y]<128)
    damage = round((dark/total)*100,2)
     
    """This is the Secondary Error Handling for the dataset which can predict infection and u can say why we add this
    because we build this dataset by our own in short time and human can mistake that's why when dataset can not predict correctly then this Error handling function will be used
    """
    
    if damage<10:        inf='healthy'
    elif damage<30:      inf='cavities'
    elif damage<50:      inf='enamel erosion'
    elif damage<70:      inf='gum infection'
    elif damage<90:      inf='abscess'
    else:                inf='periodontal disease'
    return inf, damage, infection_data.get(inf, 'No recommendation available.')

@bp.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method=='POST':
        f = request.files.get('file')
        if not f or not allowed_file(f.filename):
            flash("Please select a valid image file", "error")
            return redirect(url_for('dataset.upload'))
        fn = secure_filename(f.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        path = os.path.join(UPLOAD_FOLDER, fn)
        f.save(path)
        if not is_tooth_image(path):
            os.remove(path)
            flash("That doesn’t look like a tooth image", "error")
            return redirect(url_for('dataset.upload'))
        inf, dmg, rec = detect_infection(path)
        return render_template('result.html', infection=inf,
                               damage=dmg, recommendation=rec, filename=fn)
    return render_template('upload.html')
