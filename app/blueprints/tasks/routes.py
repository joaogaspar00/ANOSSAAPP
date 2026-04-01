from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from app.blueprints.tasks import tasks_bp
from app.blueprints.tasks.forms import TaskForm
from app.models import Task, RecurrenceRule, User
from app.extensions import db
from app.services.task_service import complete_task, sync_task_to_calendar


@tasks_bp.route("/")
@login_required
def index():
    household_id = current_user.household_id
    filter_status = request.args.get("status", "pending")

    query = Task.query.filter_by(household_id=household_id)
    if filter_status == "pending":
        query = query.filter_by(completed=False)
    elif filter_status == "done":
        query = query.filter_by(completed=True)

    tasks = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).all()
    today = date.today()
    return render_template("tasks/index.html", tasks=tasks, filter_status=filter_status, today=today)


@tasks_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    form = TaskForm()
    household_id = current_user.household_id
    users = User.query.filter_by(household_id=household_id).all()
    form.assigned_to_id.choices = [(0, "Ninguém")] + [(u.id, u.display_name) for u in users]

    if form.validate_on_submit():
        rule = None
        if form.recurrence_type.data != "none":
            rule = RecurrenceRule(
                rule_type=form.recurrence_type.data,
                interval_days=form.interval_days.data if form.recurrence_type.data == "every_x_days" else None,
            )
            db.session.add(rule)
            db.session.flush()

        task = Task(
            household_id=household_id,
            title=form.title.data,
            description=form.description.data or None,
            due_date=form.due_date.data or None,
            assigned_to_id=form.assigned_to_id.data or None,
            recurrence_rule_id=rule.id if rule else None,
        )
        db.session.add(task)
        db.session.flush()
        if task.due_date:
            sync_task_to_calendar(task)
        else:
            db.session.commit()
        flash("Tarefa criada.", "success")
        return redirect(url_for("tasks.index"))
    return render_template("tasks/form.html", form=form, editing=False)


@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, household_id=current_user.household_id).first_or_404()
    form = TaskForm(obj=task)
    users = User.query.filter_by(household_id=current_user.household_id).all()
    form.assigned_to_id.choices = [(0, "Ninguém")] + [(u.id, u.display_name) for u in users]

    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data or None
        task.due_date = form.due_date.data or None
        task.assigned_to_id = form.assigned_to_id.data or None
        db.session.commit()
        flash("Tarefa atualizada.", "success")
        return redirect(url_for("tasks.index"))
    # Pre-fill recurrence
    if task.recurrence_rule:
        form.recurrence_type.data = task.recurrence_rule.rule_type
        form.interval_days.data = task.recurrence_rule.interval_days
    return render_template("tasks/form.html", form=form, editing=True, task=task)


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@login_required
def complete(task_id):
    task = Task.query.filter_by(id=task_id, household_id=current_user.household_id).first_or_404()
    next_task = complete_task(task)
    if next_task:
        flash(f"Tarefa concluída. Próxima: {next_task.due_date}", "success")
    else:
        flash("Tarefa marcada como concluída.", "success")
    return redirect(url_for("tasks.index"))


@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, household_id=current_user.household_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Tarefa eliminada.", "info")
    return redirect(url_for("tasks.index"))
