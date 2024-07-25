#app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import csv
import io
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
admin = Admin(app, 'Anova Pulse', template_mode='bootstrap4')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)  # Increase length for hashed passwords
    payment_status = db.Column(db.String(7), default='Pending')
    is_admin = db.Column(db.Boolean, default=False)
    csv_uploaded = db.Column(db.Boolean, default=False)  # New field to track CSV upload status
    products = db.relationship('Product', back_populates='user')
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __str__(self):
        return self.name

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    produit = db.Column(db.String(100), nullable=False)
    ppv = db.Column(db.String(100), nullable=False)
    pph = db.Column(db.String(100), nullable=False)
    code_barre = db.Column(db.String(100), nullable=False)
    user = db.relationship('User', back_populates='products')

class UserController(ModelView):
    can_delete = False
    column_exclude_list = ['password']
    column_editable_list = ['payment_status']
    form_excluded_columns = ['password', 'email', 'is_admin']

    def is_accessible(self):
        if current_user.is_authenticated and current_user.is_admin:
            return True
        return abort(404)

    def not_auth(self):
        return "You are not admin"

class LogoutMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated
    
class DashboardMenuLink(MenuLink):
    def is_accessible(self):
        return current_user.is_authenticated

class ProductController(ModelView):
    can_delete = False
    can_export = True
    
    def is_accessible(self):
        if current_user.is_authenticated and current_user.is_admin:
            return True
        return abort(404)

    def not_auth(self):
        return "You are not admin"

admin.add_view(UserController(User, db.session))
admin.add_view(ProductController(Product, db.session))
admin._menu = admin._menu[1:]
admin.add_link(DashboardMenuLink(name='Dashboard', category='', url='/dashboard'))
admin.add_link(LogoutMenuLink(name='Logout', category='', url='/logout'))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if current_user.is_admin:
                return redirect('/admin')
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.filter_by(user_id=current_user.id).all()
    csv_uploaded = current_user.csv_uploaded
    return render_template('dashboard.html', products=products, csv_uploaded=csv_uploaded)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part in the request'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
    barcodes = decode(img)
    barcode_data = None
    if (barcodes):
        barcode_data = barcodes[0].data.decode('utf-8')
        return jsonify({'barcode': barcode_data})
    return jsonify({'error': 'No barcode found in image'}), 400

@app.route('/upload_csv', methods=['POST'])
@login_required
def upload_csv():
    if 'csvfile' not in request.files:
        return jsonify({'error': 'No CSV part in the request'}), 400

    file = request.files['csvfile']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Read CSV file and store data in the database
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)

        # Delete existing products for the current user to avoid duplicates
        Product.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        for row in reader:
            product = Product(
                user_id=current_user.id,
                produit=row.get('PRODUIT', 'No Product Found'),
                ppv=row.get('PPV', 'No PPV Found'),
                pph=row.get('PPH', 'No PPH Found'),
                code_barre=row.get('Code barre', '').strip()
            )
            db.session.add(product)
        db.session.commit()
        
        # Set csv_uploaded to True in the database
        current_user.csv_uploaded = True
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

    return jsonify({'message': 'CSV file uploaded and data stored successfully'}), 200

@app.route('/fetch_row', methods=['POST'])
@login_required
def fetch_row():
    barcode = request.json.get('barcode')
    if not barcode:
        return jsonify({'error': 'No barcode provided'}), 400

    product = Product.query.filter_by(user_id=current_user.id, code_barre=barcode.strip()).first()

    if product:
        return jsonify({
            'produit': product.produit,
            'ppv': product.ppv,
            'pph': product.pph,
            'categorie': '',  # Include category if available in your data
            'tva': ''  # Include tva if available in your data
        })
    return jsonify({'error': 'Barcode not found in database'}), 404

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('signup'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists')
            return redirect(url_for('signup'))

        new_user = User(name=name, email=email)
        new_user.set_password(password)  # Hash the password before saving
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
