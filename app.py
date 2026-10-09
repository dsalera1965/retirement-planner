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
    monthly_income = db.Column(db.Float, default=0)
    monthly_expenses = db.Column(db.Float, default=0)
    monthly_investment = db.Column(db.Float, default=0)
    current_debt = db.Column(db.Float, default=0)
    annual_return = db.Column(db.Float, default=0.07)
    inflation = db.Column(db.Float, default=0.03)
    desired_income = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

    if not Profile.query.first():
        db.session.add(Profile(
            name='Sample User',
            age=35,
            retirement_age=65,
            current_savings=150000,
            monthly_income=6500,
            monthly_expenses=3500,
            monthly_investment=1200,
            current_debt=25000,
            annual_return=0.07,
            inflation=0.03,
            desired_income=5000,
        ))
        db.session.commit()


def calculate_retirement(profile):
    years_to_retirement = max(profile.retirement_age - profile.age, 1)
    future_value = profile.current_savings
    monthly_rate = profile.annual_return / 12

    for _ in range(years_to_retirement * 12):
        future_value = future_value * (1 + monthly_rate)
        future_value += profile.monthly_investment

    annual_spending = profile.monthly_expenses * 12
    annual_income = profile.monthly_income * 12
    annual_gap = max(annual_spending - annual_income, 0)

    retirement_income = future_value * 0.04
    projected_gap = max(profile.desired_income - retirement_income, 0)

    return {
        'years_to_retirement': years_to_retirement,
        'projected_savings': future_value,
        'retirement_income': retirement_income,
        'annual_gap': annual_gap,
        'projected_gap': projected_gap,
        'net_monthly_cashflow': profile.monthly_income - profile.monthly_expenses,
        'savings_rate': (profile.monthly_investment / max(profile.monthly_income, 1)) * 100,
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
        profile.monthly_income = float(request.form['monthly_income'])
        profile.monthly_expenses = float(request.form['monthly_expenses'])
        profile.monthly_investment = float(request.form['monthly_investment'])
        profile.current_debt = float(request.form['current_debt'])
        profile.annual_return = float(request.form['annual_return']) / 100
        profile.inflation = float(request.form['inflation']) / 100
        profile.desired_income = float(request.form['desired_income'])
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
