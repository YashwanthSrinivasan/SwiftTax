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


class PersonalInfo(db.Model):
    __tablename__ = 'personal_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    full_name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    pan_number = db.Column(db.String(10), unique=True, nullable=False)
    aadhaar_number = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    residential_status = db.Column(db.String(50), nullable=False)
    
class BusinessInfo(db.Model):
    __tablename__ = 'business_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    business_name = db.Column(db.String(100))
    business_type = db.Column(db.String(50))
    msme_reg_number = db.Column(db.String(50))
    udyam_registration = db.Column(db.String(50))
    industry_sector = db.Column(db.String(50))
    state_of_operation = db.Column(db.String(50))
    business_address = db.Column(db.Text)
    nature_of_business = db.Column(db.Text)

class FinancialInfo(db.Model):
    __tablename__ = 'financial_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    gross_revenue = db.Column(db.Float)
    net_profit = db.Column(db.Float)
    capital_invested = db.Column(db.Float)
    projected_turnover = db.Column(db.Float)
    salaries_paid = db.Column(db.Float)
    exempt_income = db.Column(db.Float)
    foreign_income = db.Column(db.Float)
    tds_deducted = db.Column(db.Float)
    advance_tax_paid = db.Column(db.Float)
    bank_account_details = db.Column(db.Text)

class TaxInfo(db.Model):
    __tablename__ = 'tax_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    gst_registered = db.Column(db.Boolean, default=False)
    gstin_number = db.Column(db.String(15))
    gst_registration_date = db.Column(db.Date)
    composition_scheme = db.Column(db.Boolean, default=False)
    tax_regime = db.Column(db.String(20))
    filing_status = db.Column(db.String(50))
    previous_itr_type = db.Column(db.String(50))
    previous_refund_dues = db.Column(db.Float)


def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        if Account.query.count() == 0:
            account = Account(name='Main Account', balance=0.0)
            db.session.add(account)
            db.session.commit()