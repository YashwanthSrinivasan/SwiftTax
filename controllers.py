from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.sql import func, cast
from datetime import date, datetime, timedelta
from uuid import uuid4
import math

main = Blueprint('main', __name__)


def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('main.login'))
    return inner


@main.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return redirect(url_for('main.dashboard'))
    return render_template('home.html')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Please fill out all fields')
            return redirect(url_for('main.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash('Username does not exist')
            return redirect(url_for('main.login'))
        
        if not check_password_hash(user.passhash, password):
            flash('Incorrect password')
            return redirect(url_for('main.login'))
        
        session['user_id'] = user.id
        return redirect(url_for('main.index'))

    return render_template('login.html')

@main.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')

        if not username or not password or not confirm_password or not name:
            flash('Please fill out all fields')
            return redirect(url_for('main.register'))
        
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('main.register'))
        
        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists')
            return redirect(url_for('main.register'))
        
        password_hash = generate_password_hash(password)
        
        new_user = User(username=username, passhash=password_hash, name=name)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('main.login'))

@main.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('main.login'))

@main.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)