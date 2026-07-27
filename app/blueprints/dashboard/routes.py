from flask import render_template
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.blueprints.dashboard import dashboard_bp
from app.models import Task, MealPlan, InventoryItem, Expense, Activity
from app.utils import household_required, calculate_balance


@dashboard_bp.route("/")
@login_required
@household_required
def index():
    household = current_user.household
    household_id = household.id
    today = date.today()
    week_start = today
    week_end = today + timedelta(days=7)

    # Upcoming tasks (next 7 days, not done)
    upcoming_tasks = Task.query.filter(
        Task.household_id == household_id,
        Task.status != "done",
        Task.due_date != None,
        Task.due_date <= week_end,
    ).order_by(Task.due_date).limit(5).all()

    # Today's meals
    todays_meals = MealPlan.query.filter_by(
        household_id=household_id,
        planned_date=today,
    ).all()

    # Low inventory alerts
    low_inventory = [
        item for item in
        InventoryItem.query.filter_by(household_id=household_id).all()
        if item.is_low
    ]

    # Weekly cost estimate (planned meals this week)
    weekly_meals = MealPlan.query.filter(
        MealPlan.household_id == household_id,
        MealPlan.planned_date >= week_start,
        MealPlan.planned_date <= week_end,
    ).all()
    weekly_cost = sum(
        m.recipe.cost_per_serving * (m.servings_planned or 2)
        for m in weekly_meals if m.recipe
    )

    # Monthly spending (current month)
    first_of_month = today.replace(day=1)
    monthly_expenses = Expense.query.filter(
        Expense.household_id == household_id,
        Expense.date >= first_of_month,
    ).all()
    monthly_total = sum(e.amount for e in monthly_expenses)

    partner = household.partner(current_user)
    balance = calculate_balance(household, current_user, partner)

    recent_partner_activities = []
    if partner:
        recent_partner_activities = Activity.query.filter_by(
            household_id=household_id, created_by_id=partner.id
        ).order_by(Activity.created_at.desc()).limit(3).all()

    return render_template(
        "dashboard/index.html",
        upcoming_tasks=upcoming_tasks,
        todays_meals=todays_meals,
        low_inventory=low_inventory,
        weekly_cost=weekly_cost,
        monthly_total=monthly_total,
        balance=balance,
        partner=partner,
        recent_partner_activities=recent_partner_activities,
        today=today,
    )
