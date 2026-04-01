from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta
import calendar as cal_lib
from app.blueprints.calendar import calendar_bp
from app.models import CalendarEvent, Task, MealPlan
from app.extensions import db
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, BooleanField, SubmitField, TimeField
from wtforms.validators import DataRequired, Optional


class EventForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired()])
    event_type = SelectField("Tipo", choices=[
        ("external", "Evento"),
        ("shopping", "Dia de compras"),
    ])
    start_date = DateField("Data", validators=[DataRequired()])
    notes = TextAreaField("Notas", validators=[Optional()])
    submit = SubmitField("Guardar")


@calendar_bp.route("/")
@login_required
def index():
    household_id = current_user.household_id
    today = date.today()
    # Week view: Mon–Sun of current (or requested) week
    week_offset = request.args.get("week", 0, type=int)
    week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_days = [week_start + timedelta(days=i) for i in range(7)]

    # Fetch events for the week
    events = CalendarEvent.query.filter(
        CalendarEvent.household_id == household_id,
        CalendarEvent.start_date >= week_days[0],
        CalendarEvent.start_date <= week_days[-1],
    ).all()

    # Fetch tasks with due dates this week
    tasks = Task.query.filter(
        Task.household_id == household_id,
        Task.due_date >= week_days[0],
        Task.due_date <= week_days[-1],
        Task.completed == False,
    ).all()

    # Fetch meal plans
    meals = MealPlan.query.filter(
        MealPlan.household_id == household_id,
        MealPlan.planned_date >= week_days[0],
        MealPlan.planned_date <= week_days[-1],
    ).all()

    # Build day → items map
    day_map = {d: {"events": [], "tasks": [], "meals": []} for d in week_days}
    for e in events:
        if e.start_date in day_map:
            day_map[e.start_date]["events"].append(e)
    for t in tasks:
        if t.due_date in day_map:
            day_map[t.due_date]["tasks"].append(t)
    for m in meals:
        if m.planned_date in day_map:
            day_map[m.planned_date]["meals"].append(m)

    form = EventForm()
    return render_template(
        "calendar/index.html",
        week_days=week_days,
        day_map=day_map,
        week_offset=week_offset,
        today=today,
        form=form,
    )


@calendar_bp.route("/add", methods=["POST"])
@login_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        event = CalendarEvent(
            household_id=current_user.household_id,
            title=form.title.data,
            event_type=form.event_type.data,
            start_date=form.start_date.data,
            notes=form.notes.data or None,
        )
        db.session.add(event)
        db.session.commit()
        flash("Evento adicionado.", "success")
    return redirect(url_for("calendar.index"))


@calendar_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def delete_event(event_id):
    event = CalendarEvent.query.filter_by(
        id=event_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(event)
    db.session.commit()
    flash("Evento eliminado.", "info")
    return redirect(url_for("calendar.index"))
