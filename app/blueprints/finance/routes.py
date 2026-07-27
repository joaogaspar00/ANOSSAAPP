import csv
import io
from flask import render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from datetime import date
from sqlalchemy import extract, func
from app.blueprints.finance import finance_bp
from app.blueprints.finance.forms import ExpenseForm
from app.models import Expense, Settlement, EXPENSE_CATEGORIES
from app.extensions import db
from app.utils import household_required, calculate_balance


def _payer_choices(household):
    return [(u.id, u.display_name) for u in household.members()]


@finance_bp.route("/")
@login_required
@household_required
def index():
    household = current_user.household
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    expenses = Expense.query.filter(
        Expense.household_id == household.id,
        extract("month", Expense.date) == month,
        extract("year", Expense.date) == year,
    ).order_by(Expense.date.desc()).all()

    total = sum(e.amount for e in expenses)

    by_category = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0) + e.amount

    trend = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        monthly_sum = db.session.query(func.sum(Expense.amount)).filter(
            Expense.household_id == household.id,
            extract("month", Expense.date) == m,
            extract("year", Expense.date) == y,
        ).scalar() or 0
        trend.append({"month": f"{y}-{m:02d}", "total": round(monthly_sum, 2)})

    partner = household.partner(current_user)
    balance = calculate_balance(household, current_user, partner)

    return render_template(
        "finance/index.html",
        expenses=expenses,
        total=total,
        by_category=by_category,
        trend=trend,
        month=month,
        year=year,
        categories=EXPENSE_CATEGORIES,
        balance=balance,
        partner=partner,
    )


@finance_bp.route("/add", methods=["GET", "POST"])
@login_required
@household_required
def add():
    household = current_user.household
    form = ExpenseForm()
    form.paid_by_id.choices = _payer_choices(household)
    if not form.date.data:
        form.date.data = date.today()
    if request.method == "GET":
        form.paid_by_id.data = current_user.id

    if form.validate_on_submit():
        expense = Expense(
            household_id=household.id,
            date=form.date.data,
            category=form.category.data,
            amount=form.amount.data,
            paid_by_id=form.paid_by_id.data,
            split_type=form.split_type.data,
            amount_a=form.amount_a.data or 0,
            amount_b=form.amount_b.data or 0,
            note=form.note.data or None,
        )
        if expense.split_type != "custom":
            expense.compute_split()
        db.session.add(expense)
        db.session.commit()
        flash("Despesa registada.", "success")
        return redirect(url_for("finance.index"))
    return render_template("finance/add.html", form=form, editing=False)


@finance_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit(expense_id):
    household = current_user.household
    expense = Expense.query.filter_by(id=expense_id, household_id=household.id).first_or_404()
    form = ExpenseForm(obj=expense)
    form.paid_by_id.choices = _payer_choices(household)

    if form.validate_on_submit():
        expense.date = form.date.data
        expense.category = form.category.data
        expense.amount = form.amount.data
        expense.paid_by_id = form.paid_by_id.data
        expense.split_type = form.split_type.data
        expense.amount_a = form.amount_a.data or 0
        expense.amount_b = form.amount_b.data or 0
        expense.note = form.note.data or None
        if expense.split_type != "custom":
            expense.compute_split()
        db.session.commit()
        flash("Despesa atualizada.", "success")
        return redirect(url_for("finance.index"))
    return render_template("finance/add.html", form=form, editing=True, expense=expense)


@finance_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
@household_required
def delete(expense_id):
    expense = Expense.query.filter_by(
        id=expense_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash("Despesa eliminada.", "info")
    return redirect(url_for("finance.index"))


@finance_bp.route("/settle", methods=["POST"])
@login_required
@household_required
def settle():
    household = current_user.household
    partner = household.partner(current_user)
    balance = calculate_balance(household, current_user, partner)

    if not partner or balance["owes"] is None or balance["amount"] == 0:
        flash("Não há saldo para liquidar.", "info")
        return redirect(url_for("finance.index"))

    if balance["owes"]:
        from_user, to_user = current_user, partner
    else:
        from_user, to_user = partner, current_user

    settlement = Settlement(
        household_id=household.id,
        from_user_id=from_user.id,
        to_user_id=to_user.id,
        amount=balance["amount"],
    )
    db.session.add(settlement)
    db.session.commit()
    flash("Saldo liquidado.", "success")
    return redirect(url_for("finance.index"))


@finance_bp.route("/export")
@login_required
@household_required
def export_csv():
    household = current_user.household
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    expenses = Expense.query.filter(
        Expense.household_id == household.id,
        extract("month", Expense.date) == month,
        extract("year", Expense.date) == year,
    ).order_by(Expense.date.desc()).all()

    buffer = io.StringIO()
    buffer.write("﻿")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Data", "Categoria", "Valor", "Pago por", "Nota"])
    for e in expenses:
        writer.writerow([
            e.date.isoformat(), e.category, e.amount,
            e.paid_by.display_name if e.paid_by else "", e.note or "",
        ])

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=despesas_{year}_{month:02d}.csv"},
    )
