"""
utils.py — Shared helpers used across blueprints.
"""
from functools import wraps
from flask import redirect, url_for
from flask_login import current_user


def household_required(view):
    """Use together with @login_required: sends users with no household to onboarding."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.household_id:
            return redirect(url_for("auth.onboarding"))
        return view(*args, **kwargs)
    return wrapped


def calculate_balance(household, user, partner):
    """Nets Expense splits against Settlements between the two household members."""
    from app.models import Expense, Settlement

    if not partner:
        return {"owes": None, "amount": 0}

    members = household.members()
    if len(members) < 2:
        return {"owes": None, "amount": 0}

    user_a, user_b = members[0], members[1]
    a_owes_b = 0.0
    b_owes_a = 0.0

    for expense in household.expenses:
        if expense.paid_by_id == user_b.id:
            a_owes_b += expense.amount_a
        elif expense.paid_by_id == user_a.id:
            b_owes_a += expense.amount_b

    for settlement in household.settlements:
        if settlement.from_user_id == user_a.id and settlement.to_user_id == user_b.id:
            a_owes_b -= settlement.amount
        elif settlement.from_user_id == user_b.id and settlement.to_user_id == user_a.id:
            b_owes_a -= settlement.amount

    net = a_owes_b - b_owes_a  # positive: A owes B; negative: B owes A

    if user.id == user_a.id:
        if net > 0:
            return {"owes": True, "amount": abs(net), "to": partner}
        elif net < 0:
            return {"owes": False, "amount": abs(net), "to": user}
    else:
        if net < 0:
            return {"owes": True, "amount": abs(net), "to": partner}
        elif net > 0:
            return {"owes": False, "amount": abs(net), "to": user}

    return {"owes": None, "amount": 0}
