from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///retirement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    retirement_age = db.Column(db.Integer, nullable=False)
    current_savings = db.Column(db.Float, default=0)
    monthly_expenses = db.Column(db.Float, default=0)
    monthly_investment = db.Column(db.Float, default=0)
    monthly_bonus = db.Column(db.Float, default=0)
    current_debt = db.Column(db.Float, default=0)
    annual_return = db.Column(db.Float, default=0.07)
    inflation = db.Column(db.Float, default=0.03)
    desired_income = db.Column(db.Float, default=0)
    # Current work income (pre-retirement)
    monthly_wages = db.Column(db.Float, default=0)
    # Retirement income sources
    annual_pension = db.Column(db.Float, default=0)
    annual_social_security = db.Column(db.Float, default=0)
    annual_ira_withdrawal = db.Column(db.Float, default=0)
    annual_rental_income = db.Column(db.Float, default=0)
    annual_other_income = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

    profile = Profile.query.first()
    if not profile:
        db.session.add(Profile(
            name='Sample User',
            age=35,
            retirement_age=65,
            current_savings=150000,
            monthly_wages=6500,
            monthly_bonus=1200,
            monthly_expenses=3500,
            monthly_investment=1200,
            current_debt=25000,
            annual_return=0.07,
            inflation=0.03,
            desired_income=5000,
            annual_pension=24000,
            annual_social_security=28000,
            annual_ira_withdrawal=12000,
            annual_rental_income=6000,
            annual_other_income=0,
        ))
        db.session.commit()


def calculate_retirement(profile):
    years_to_retirement = max(profile.retirement_age - profile.age, 1)
    future_value = profile.current_savings
    monthly_rate = profile.annual_return / 12

    for _ in range(years_to_retirement * 12):
        future_value = future_value * (1 + monthly_rate)
        future_value += profile.monthly_investment

    # Calculate retirement income from all sources
    annual_pension = profile.annual_pension or 0
    annual_social_security = profile.annual_social_security or 0
    annual_ira_withdrawal = profile.annual_ira_withdrawal or 0
    annual_rental_income = profile.annual_rental_income or 0
    annual_other_income = profile.annual_other_income or 0

    # Calculate portfolio withdrawal (4% rule)
    portfolio_withdrawal = future_value * 0.04

    # Total retirement income
    total_retirement_income = (annual_pension + annual_social_security +
                               annual_ira_withdrawal + annual_rental_income +
                               annual_other_income + portfolio_withdrawal)

    annual_expenses = profile.monthly_expenses * 12
    projected_gap = max(profile.desired_income - total_retirement_income, 0)

    # Current income and expenses
    annual_bonus = (profile.monthly_bonus or 0) * 12
    annual_wages = ((profile.monthly_wages or 0) + (profile.monthly_bonus or 0)) * 12
    annual_gap = max(annual_expenses - annual_wages, 0)

    return {
        'years_to_retirement': years_to_retirement,
        'projected_savings': future_value,
        'portfolio_withdrawal': portfolio_withdrawal,
        'annual_pension': annual_pension,
        'annual_social_security': annual_social_security,
        'annual_ira_withdrawal': annual_ira_withdrawal,
        'annual_rental_income': annual_rental_income,
        'annual_other_income': annual_other_income,
        'total_retirement_income': total_retirement_income,
        'annual_gap': annual_gap,
        'projected_gap': projected_gap,
        'annual_bonus': annual_bonus,
        'annual_wages': annual_wages,
        'net_monthly_cashflow': (profile.monthly_wages or 0) - profile.monthly_expenses,
        'savings_rate': (profile.monthly_investment / max(profile.monthly_wages or 1, 1)) * 100,
    }


@app.route('/')
def index():
    profile = Profile.query.first()
    if not profile:
        return redirect(url_for('setup'))

    data = calculate_retirement(profile)
    return render_template('index.html', profile=profile, data=data, max=max, min=min)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        profile = Profile.query.first() or Profile()
        profile.name = request.form['name']
        profile.age = int(request.form['age'])
        profile.retirement_age = int(request.form['retirement_age'])
        profile.current_savings = float(request.form['current_savings'])
        profile.monthly_wages = float(request.form.get('monthly_wages', 0))
        profile.monthly_bonus = float(request.form.get('monthly_bonus', 0))
        profile.monthly_expenses = float(request.form['monthly_expenses'])
        profile.monthly_investment = float(request.form['monthly_investment'])
        profile.current_debt = float(request.form['current_debt'])
        profile.annual_return = float(request.form['annual_return']) / 100
        profile.inflation = float(request.form['inflation']) / 100
        profile.desired_income = float(request.form['desired_income'])
        profile.annual_pension = float(request.form.get('annual_pension', 0))
        profile.annual_social_security = float(request.form.get('annual_social_security', 0))
        profile.annual_ira_withdrawal = float(request.form.get('annual_ira_withdrawal', 0))
        profile.annual_rental_income = float(request.form.get('annual_rental_income', 0))
        profile.annual_other_income = float(request.form.get('annual_other_income', 0))
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('index'))

    profile = Profile.query.first()
    return render_template('setup.html', profile=profile, max=max, min=min)


@app.route('/reset', methods=['POST'])
def reset_profile():
    Profile.query.delete()
    db.session.commit()
    return redirect(url_for('setup'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
