from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.goals import goals_bp
from app.blueprints.goals.forms import GoalForm, ProgressForm
from app.models import Goal, GOAL_STATUSES
from app.extensions import db
from app.utils import household_required


@goals_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    filter_status = request.args.get("status", "active")

    query = Goal.query.filter_by(household_id=household_id)
    if filter_status != "all":
        query = query.filter_by(status=filter_status)

    goals = query.order_by(Goal.created_at.desc()).all()
    return render_template(
        "goals/index.html", goals=goals, filter_status=filter_status,
        progress_form=ProgressForm(), statuses=GOAL_STATUSES,
    )


@goals_bp.route("/add", methods=["GET", "POST"])
@login_required
@household_required
def add():
    form = GoalForm()
    if form.validate_on_submit():
        goal = Goal(
            household_id=current_user.household_id,
            created_by_id=current_user.id,
            title=form.title.data,
            description=form.description.data or None,
            type=form.type.data,
            target_value=form.target_value.data,
            deadline=form.deadline.data,
        )
        db.session.add(goal)
        db.session.commit()
        flash("Objetivo criado.", "success")
        return redirect(url_for("goals.index"))
    return render_template("goals/form.html", form=form, editing=False)


@goals_bp.route("/<int:goal_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit(goal_id):
    goal = Goal.query.filter_by(id=goal_id, household_id=current_user.household_id).first_or_404()
    form = GoalForm(obj=goal)
    if form.validate_on_submit():
        goal.title = form.title.data
        goal.description = form.description.data or None
        goal.type = form.type.data
        goal.target_value = form.target_value.data
        goal.deadline = form.deadline.data
        goal.sync_status()
        db.session.commit()
        flash("Objetivo atualizado.", "success")
        return redirect(url_for("goals.index"))
    return render_template("goals/form.html", form=form, editing=True, goal=goal)


@goals_bp.route("/<int:goal_id>/progress", methods=["POST"])
@login_required
@household_required
def update_progress(goal_id):
    goal = Goal.query.filter_by(id=goal_id, household_id=current_user.household_id).first_or_404()
    form = ProgressForm()
    if form.validate_on_submit():
        goal.current_value = form.current_value.data
        goal.sync_status()
        db.session.commit()
        flash("Progresso atualizado.", "success")
    return redirect(url_for("goals.index"))


@goals_bp.route("/<int:goal_id>/pause", methods=["POST"])
@login_required
@household_required
def toggle_pause(goal_id):
    goal = Goal.query.filter_by(id=goal_id, household_id=current_user.household_id).first_or_404()
    goal.status = "paused" if goal.status == "active" else "active"
    db.session.commit()
    return redirect(url_for("goals.index"))


@goals_bp.route("/<int:goal_id>/delete", methods=["POST"])
@login_required
@household_required
def delete(goal_id):
    goal = Goal.query.filter_by(id=goal_id, household_id=current_user.household_id).first_or_404()
    db.session.delete(goal)
    db.session.commit()
    flash("Objetivo eliminado.", "info")
    return redirect(url_for("goals.index"))
