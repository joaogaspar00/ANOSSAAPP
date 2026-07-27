from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
import calendar as cal_lib
from app.blueprints.calendar import calendar_bp
from app.blueprints.calendar.forms import EventForm
from app.models import CalendarEvent, Task, MealPlan
from app.extensions import db
from app.utils import household_required

MONTH_NAMES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


@calendar_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    first_weekday, days_in_month = cal_lib.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    events = [
        e for e in CalendarEvent.query.filter(
            CalendarEvent.household_id == household_id,
            CalendarEvent.start_date >= month_start,
            CalendarEvent.start_date <= month_end,
        ).all()
        if e.visible_to(current_user)
    ]
    tasks = Task.query.filter(
        Task.household_id == household_id,
        Task.due_date >= month_start,
        Task.due_date <= month_end,
        Task.status != "done",
    ).all()
    meals = MealPlan.query.filter(
        MealPlan.household_id == household_id,
        MealPlan.planned_date >= month_start,
        MealPlan.planned_date <= month_end,
    ).all()

    events_by_day = {d: [] for d in range(1, days_in_month + 1)}
    for e in events:
        events_by_day[e.start_date.day].append({"kind": "event", "obj": e})
    for t in tasks:
        events_by_day[t.due_date.day].append({"kind": "task", "obj": t})
    for m in meals:
        events_by_day[m.planned_date.day].append({"kind": "meal", "obj": m})

    weeks = cal_lib.monthcalendar(year, month)
    form = EventForm()

    return render_template(
        "calendar/index.html",
        weeks=weeks,
        events_by_day=events_by_day,
        month=month,
        year=year,
        month_name=MONTH_NAMES[month],
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        today=today,
        form=form,
    )


@calendar_bp.route("/add", methods=["POST"])
@login_required
@household_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        event = CalendarEvent(
            household_id=current_user.household_id,
            owner_id=current_user.id,
            title=form.title.data,
            event_type=form.event_type.data,
            visibility=form.visibility.data,
            start_date=form.start_date.data,
            notes=form.notes.data or None,
        )
        db.session.add(event)
        db.session.commit()
        flash("Evento adicionado.", "success")
    return redirect(url_for("calendar.index", month=request.args.get("month"), year=request.args.get("year")))


@calendar_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit_event(event_id):
    event = CalendarEvent.query.filter_by(
        id=event_id, household_id=current_user.household_id
    ).first_or_404()
    form = EventForm(obj=event)
    if form.validate_on_submit():
        event.title = form.title.data
        event.event_type = form.event_type.data
        event.visibility = form.visibility.data
        event.start_date = form.start_date.data
        event.notes = form.notes.data or None
        db.session.commit()
        flash("Evento atualizado.", "success")
        return redirect(url_for("calendar.index"))
    return render_template("calendar/event_form.html", form=form, event=event)


@calendar_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
@household_required
def delete_event(event_id):
    event = CalendarEvent.query.filter_by(
        id=event_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(event)
    db.session.commit()
    flash("Evento eliminado.", "info")
    return redirect(url_for("calendar.index"))
