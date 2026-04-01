from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from sqlalchemy import extract, func
from app.blueprints.finance import finance_bp
from app.blueprints.finance.forms import ExpenseForm
from app.models import Expense, EXPENSE_CATEGORIES
from app.extensions import db


@finance_bp.route("/")
@login_required
def index():
    household_id = current_user.household_id
    today = date.today()
    # Month filter from query param, default current month
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    expenses = Expense.query.filter(
        Expense.household_id == household_id,
        extract("month", Expense.date) == month,
        extract("year", Expense.date) == year,
    ).order_by(Expense.date.desc()).all()

    total = sum(e.amount for e in expenses)

    # Spending by category
    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    # Monthly trend: last 6 months
    trend = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        monthly_sum = db.session.query(func.sum(Expense.amount)).filter(
            Expense.household_id == household_id,
            extract("month", Expense.date) == m,
            extract("year", Expense.date) == y,
        ).scalar() or 0
        trend.append({"month": f"{y}-{m:02d}", "total": round(monthly_sum, 2)})

    return render_template(
        "finance/index.html",
        expenses=expenses,
        total=total,
        by_category=by_category,
        trend=trend,
        month=month,
        year=year,
        categories=EXPENSE_CATEGORIES,
    )


@finance_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = ExpenseForm()
    if not form.date.data:
        form.date.data = date.today()
    if form.validate_on_submit():
        expense = Expense(
            household_id=current_user.household_id,
            date=form.date.data,
            category=form.category.data,
            amount=form.amount.data,
            note=form.note.data or None,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Despesa registada.", "success")
        return redirect(url_for("finance.index"))
    return render_template("finance/add.html", form=form)


@finance_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete(expense_id):
    expense = Expense.query.filter_by(
        id=expense_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Despesa eliminada.", "info")
    return redirect(url_for("finance.index"))
