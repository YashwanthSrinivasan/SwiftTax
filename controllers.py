from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, Expense, Income, Account, PersonalInfo, BusinessInfo, FinancialInfo, TaxInfo
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy.sql import func, cast
from datetime import date, datetime, timedelta
from uuid import uuid4

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

        if user.first_login:
            # Update the first_login status to False
            user.first_login = False
            db.session.commit()
            return redirect(url_for('main.first_login'))  # Redirect to first login page
        else:
            return redirect(url_for('main.dashboard'))

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

@main.route('/logout', methods=['POST'])  # Change to POST
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('main.login'))

@main.route('/first_login', methods=['GET', 'POST'])
@auth_required
def first_login():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            # Personal Info
            personal = PersonalInfo(
                user_id=user.id,
                full_name=request.form['full_name'],
                dob=datetime.strptime(request.form['dob'], '%Y-%m-%d').date(),
                pan_number=request.form['pan_number'],
                aadhaar_number=request.form['aadhaar_number'],
                email=request.form['email'],
                mobile=request.form['mobile'],
                residential_status=request.form['residential_status']
            )
            db.session.add(personal)
            
            # Business Info
            business = BusinessInfo(
                user_id=user.id,
                business_name=request.form.get('business_name'),
                business_type=request.form.get('business_type'),
                msme_reg_number=request.form.get('msme_reg_number'),
                udyam_registration=request.form.get('udyam_registration'),
                industry_sector=request.form.get('industry_sector'),
                state_of_operation=request.form.get('state_of_operation'),
                business_address=request.form.get('business_address'),
                nature_of_business=request.form.get('nature_of_business')
            )
            db.session.add(business)
            
            # Financial Info
            financial = FinancialInfo(
                user_id=user.id,
                gross_revenue=float(request.form.get('gross_revenue', 0)),
                net_profit=float(request.form.get('net_profit', 0)),
                capital_invested=float(request.form.get('capital_invested', 0)),
                projected_turnover=float(request.form.get('projected_turnover', 0)),
                salaries_paid=float(request.form.get('salaries_paid', 0)),
                exempt_income=float(request.form.get('exempt_income', 0)),
                foreign_income=float(request.form.get('foreign_income', 0)),
                tds_deducted=float(request.form.get('tds_deducted', 0)),
                advance_tax_paid=float(request.form.get('advance_tax_paid', 0)),
                bank_account_details=request.form.get('bank_account_details')
            )
            db.session.add(financial)
            
            # Tax Info
            tax = TaxInfo(
                user_id=user.id,
                gst_registered='gst_registered' in request.form,
                gstin_number=request.form.get('gstin_number'),
                gst_registration_date=datetime.strptime(request.form['gst_registration_date'], '%Y-%m-%d').date() if request.form.get('gst_registration_date') else None,
                composition_scheme='composition_scheme' in request.form,
                tax_regime=request.form.get('tax_regime'),
                filing_status=request.form.get('filing_status'),
                previous_itr_type=request.form.get('previous_itr_type'),
                previous_refund_dues=float(request.form.get('previous_refund_dues', 0))
            )
            db.session.add(tax)
            
            user.first_login = False
            db.session.commit()
            flash('Registration complete!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving data: {str(e)}', 'danger')
    
    return render_template('first_login.html')



@main.route('/dashboard', methods=['GET'])
@auth_required
def dashboard():
    account = Account.query.first()
    user_id = session['user_id']
    
    # Calculate totals for last 30 days
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    
    total_income = db.session.query(func.sum(Income.amount)).filter(
        Income.date >= thirty_days_ago
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.date >= thirty_days_ago
    ).scalar() or 0
    
    # Get recent transactions
    recent_transactions = []
    recent_incomes = Income.query.order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    
    for income in recent_incomes:
        recent_transactions.append({
            'type': 'income',
            'date': income.date,
            'description': income.description,
            'amount': income.amount,
            'category': income.category
        })
    
    for expense in recent_expenses:
        recent_transactions.append({
            'type': 'expense',
            'date': expense.date,
            'description': expense.description,
            'amount': expense.amount,
            'category': expense.category
        })
    
    # Sort by date
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    personal_info = PersonalInfo.query.filter_by(user_id=user_id).first()
    business_info = BusinessInfo.query.filter_by(user_id=user_id).first()
    financial_info = FinancialInfo.query.filter_by(user_id=user_id).first()
    tax_info = TaxInfo.query.filter_by(user_id=user_id).first()

    # Existing financial calculations
    # ...

    return render_template('dashboard.html',
        personal_info=personal_info,
        business_info=business_info,
        financial_info=financial_info,
        tax_info=tax_info,
        # Existing variables
        account=account,
        total_income=total_income,
        total_expenses=total_expenses,
        recent_transactions=recent_transactions[:5])

# Data for charts
@main.route('/chart-data')
def chart_data():
    # Last 6 months data
    months = []
    income_data = []
    expense_data = []
    
    for i in range(5, -1, -1):
        month_start = (datetime.utcnow().replace(day=1) - timedelta(days=30*i)).date()
        month_name = month_start.strftime('%b %Y')
        months.append(month_name)
        
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        income = db.session.query(func.sum(Income.amount)).filter(
            Income.date >= month_start,
            Income.date <= month_end
        ).scalar() or 0
        
        expense = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date >= month_start,
            Expense.date <= month_end
        ).scalar() or 0
        
        income_data.append(float(income))
        expense_data.append(float(expense))
    
    return jsonify({
        'months': months,
        'income': income_data,
        'expenses': expense_data
    })

# Expense Routes (updated to update account balance)
@main.route('/expenses')
def expenses():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=expenses)

@main.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        account = Account.query.first()
        invoice_number = request.form['invoice_number']
        description = request.form['description']
        amount = float(request.form['amount'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        category = request.form['category']
        from_person = request.form['from_person']
        to_person = request.form['to_person']
        payment_method = request.form['payment_method']
        
        if Expense.query.filter_by(invoice_number=invoice_number).first():
            flash('Invoice number already exists!', 'danger')
            return redirect(url_for('main.add_expense'))
        
        expense = Expense(
            invoice_number=invoice_number,
            description=description,
            amount=amount,
            date=date,
            category=category,
            from_person=from_person,
            to_person=to_person,
            payment_method=payment_method,
            account_id=account.id
        )
        
        db.session.add(expense)
        account.update_balance(amount)
        db.session.commit()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.expenses'))
    
    return render_template('add_expense.html')

# Income Routes (updated to update account balance)
@main.route('/incomes')
def incomes():
    incomes = Income.query.order_by(Income.date.desc()).all()
    return render_template('incomes.html', incomes=incomes)

@main.route('/add_income', methods=['GET', 'POST'])
def add_income():
    if request.method == 'POST':
        account = Account.query.first()
        invoice_number = request.form['invoice_number']
        description = request.form['description']
        amount = float(request.form['amount'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        category = request.form['category']
        from_person = request.form['from_person']
        to_person = request.form['to_person']
        payment_method = request.form['payment_method']
        
        if Income.query.filter_by(invoice_number=invoice_number).first():
            flash('Invoice number already exists!', 'danger')
            return redirect(url_for('main.add_income'))
        
        income = Income(
            invoice_number=invoice_number,
            description=description,
            amount=amount,
            date=date,
            category=category,
            from_person=from_person,
            to_person=to_person,
            payment_method=payment_method,
            account_id=account.id
        )
        
        db.session.add(income)
        account.update_balance(amount, is_income=True)
        db.session.commit()
        flash('Income added successfully!', 'success')
        return redirect(url_for('main.incomes'))
    
    return render_template('add_income.html')

@main.route('/settings', methods=['GET', 'POST'])
@auth_required
def settings():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # Update name
        user.name = request.form.get('name', user.name)
        
        # Password change logic
        if request.form.get('current_password'):
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not check_password_hash(user.passhash, current_password):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            else:
                user.passhash = generate_password_hash(new_password)
                flash('Password updated successfully', 'success')
        
        db.session.commit()
        return redirect(url_for('main.settings'))
    
    return render_template('settings.html', user=user)

@main.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@auth_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    account = Account.query.first()
    if request.method == 'POST':
        # Update the expense details
        old_amount= expense.amount
        expense.description = request.form['description']
        expense.amount = float(request.form['amount'])
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        expense.category = request.form['category']
        account.update_balance(old_amount - expense.amount, is_income=True)
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('main.expenses'))

    return render_template('edit_expense.html', expense=expense)

@main.route('/delete_expense/<int:expense_id>', methods=['POST'])
@auth_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    # Update account balance when deleting an expense
    account = Account.query.first()
    account.update_balance(expense.amount, is_income=False)

    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('main.expenses'))

@main.route('/edit_income/<int:income_id>', methods=['GET', 'POST'])
@auth_required
def edit_income(income_id):
    income = Income.query.get_or_404(income_id)
    account = Account.query.first()
    if request.method == 'POST':
        # Update the income details
        old_amount = income.amount
        income.description = request.form['description']
        income.amount = float(request.form['amount'])
        income.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        income.category = request.form['category']
        
        account.update_balance(income.amount - old_amount, is_income=True)
        db.session.commit()
        flash('Income updated successfully!', 'success')
        return redirect(url_for('main.incomes'))

    return render_template('edit_income.html', income=income)

@main.route('/delete_income/<int:income_id>', methods=['POST'])
@auth_required
def delete_income(income_id):
    income = Income.query.get_or_404(income_id)

    # Update account balance when deleting an income
    account = Account.query.first()
    account.update_balance(-income.amount, is_income=True)

    db.session.delete(income)
    db.session.commit()
    flash('Income deleted successfully!', 'success')
    return redirect(url_for('main.incomes'))

@main.route('/gst_filing')
@auth_required
def gst_filing():
    return render_template('gst_filing.html')
