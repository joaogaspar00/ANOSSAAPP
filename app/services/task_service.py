"""
services/task_service.py — Recurring Task Scheduler

When a recurring task is marked complete, this service creates the
next occurrence automatically. It also generates CalendarEvents for tasks.
"""
from datetime import date, timedelta
from app.extensions import db
from app.models import Task, CalendarEvent, RecurrenceRule
import logging

logger = logging.getLogger(__name__)


def complete_task(task: Task) -> Task | None:
    """
    Mark a task complete and, if recurring, generate the next occurrence.
    Returns the new task if one was created, else None.
    """
    from datetime import datetime
    task.status = "done"
    task.completed_at = datetime.utcnow()
    db.session.flush()

    next_task = None
    if task.recurrence_rule and task.recurrence_rule.rule_type != "none":
        next_due = _next_due_date(task)
        if next_due:
            next_task = Task(
                household_id=task.household_id,
                assigned_to_id=task.assigned_to_id,
                recurrence_rule_id=task.recurrence_rule_id,
                title=task.title,
                description=task.description,
                due_date=next_due,
                priority=task.priority,
                status="pending",
            )
            db.session.add(next_task)
            db.session.flush()
            _create_calendar_event(next_task)

    db.session.commit()
    return next_task


def _next_due_date(task: Task) -> date | None:
    rule = task.recurrence_rule
    base = task.due_date or date.today()

    if rule.rule_type == "daily":
        return base + timedelta(days=1)
    elif rule.rule_type == "weekly":
        return base + timedelta(weeks=1)
    elif rule.rule_type == "monthly":
        # Same day next month
        month = base.month + 1
        year = base.year
        if month > 12:
            month = 1
            year += 1
        try:
            return base.replace(year=year, month=month)
        except ValueError:
            # Edge case: e.g. Jan 31 → Feb 28
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            return base.replace(year=year, month=month, day=last_day)
    elif rule.rule_type == "every_x_days" and rule.interval_days:
        return base + timedelta(days=rule.interval_days)
    return None


def _create_calendar_event(task: Task):
    """Sync a task to the calendar."""
    if not task.due_date:
        return
    # Avoid duplicates
    existing = CalendarEvent.query.filter_by(source_task_id=task.id).first()
    if existing:
        existing.start_date = task.due_date
        existing.title = task.title
    else:
        event = CalendarEvent(
            household_id=task.household_id,
            title=task.title,
            event_type="task",
            start_date=task.due_date,
            all_day=True,
            source_task_id=task.id,
        )
        db.session.add(event)


def sync_task_to_calendar(task: Task):
    """Public helper to sync any task to the calendar."""
    _create_calendar_event(task)
    db.session.commit()
