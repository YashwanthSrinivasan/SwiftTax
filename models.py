import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    first_login = db.Column(db.Boolean, default=True, nullable=False)

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Main Account')
    balance = db.Column(db.Float, nullable=False, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def update_balance(self, amount, is_income=False):
        if is_income:
            self.balance += amount
        else:
            self.balance -= amount
        self.last_updated = datetime.utcnow()
        db.session.commit()

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    from_person = db.Column(db.String(100), nullable=True)
    to_person = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    def __repr__(self):
        return f'<Expense {self.invoice_number}>'

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    category = db.Column(db.String(50), nullable=False)
    from_person = db.Column(db.String(100), nullable=True)
    to_person = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)

    def __repr__(self):
        return f'<Income {self.invoice_number}>'
    
def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if Account.query.count() == 0:
            account = Account(name='Main Account', balance=0.0)
            db.session.add(account)
            db.session.commit()