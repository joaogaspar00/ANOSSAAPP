from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from app.blueprints.activities import activities_bp
from app.blueprints.activities.forms import ActivityForm, RatingForm
from app.models import Activity, ACTIVITY_STATUSES
from app.extensions import db
from app.utils import household_required

STATUS_ORDER = ["wishlist", "planned", "done"]


@activities_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    filter_type = request.args.get("type")
    filter_status = request.args.get("status")

    query = Activity.query.filter_by(household_id=household_id)
    if filter_type:
        query = query.filter_by(type=filter_type)
    if filter_status:
        query = query.filter_by(status=filter_status)

    activities = query.order_by(Activity.created_at.desc()).all()
    return render_template(
        "activities/index.html", activities=activities,
        filter_type=filter_type, filter_status=filter_status,
        rating_form=RatingForm(), statuses=ACTIVITY_STATUSES,
    )


@activities_bp.route("/add", methods=["GET", "POST"])
@login_required
@household_required
def add():
    form = ActivityForm()
    if form.validate_on_submit():
        activity = Activity(
            household_id=current_user.household_id,
            created_by_id=current_user.id,
            name=form.name.data,
            type=form.type.data,
            planned_date=form.planned_date.data,
            location=form.location.data or None,
            notes=form.notes.data or None,
        )
        db.session.add(activity)
        db.session.commit()
        flash("Atividade adicionada à wishlist.", "success")
        return redirect(url_for("activities.index"))
    return render_template("activities/form.html", form=form, editing=False)


@activities_bp.route("/<int:activity_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit(activity_id):
    activity = Activity.query.filter_by(id=activity_id, household_id=current_user.household_id).first_or_404()
    form = ActivityForm(obj=activity)
    if form.validate_on_submit():
        activity.name = form.name.data
        activity.type = form.type.data
        activity.planned_date = form.planned_date.data
        activity.location = form.location.data or None
        activity.notes = form.notes.data or None
        db.session.commit()
        flash("Atividade atualizada.", "success")
        return redirect(url_for("activities.index"))
    return render_template("activities/form.html", form=form, editing=True, activity=activity)


@activities_bp.route("/<int:activity_id>/move", methods=["POST"])
@login_required
@household_required
def move_status(activity_id):
    activity = Activity.query.filter_by(id=activity_id, household_id=current_user.household_id).first_or_404()
    new_status = request.form.get("status")
    if new_status not in STATUS_ORDER:
        flash("Estado inválido.", "danger")
        return redirect(url_for("activities.index"))
    activity.status = new_status
    if new_status == "done" and not activity.done_date:
        activity.done_date = date.today()
    db.session.commit()
    flash("Estado atualizado.", "success")
    return redirect(url_for("activities.index"))


@activities_bp.route("/<int:activity_id>/rate", methods=["POST"])
@login_required
@household_required
def rate(activity_id):
    activity = Activity.query.filter_by(id=activity_id, household_id=current_user.household_id).first_or_404()
    if activity.status != "done":
        flash("Só podes avaliar atividades já feitas.", "danger")
        return redirect(url_for("activities.index"))
    form = RatingForm()
    if form.validate_on_submit():
        activity.set_rating(current_user, form.value.data)
        db.session.commit()
        flash("Avaliação guardada.", "success")
    return redirect(url_for("activities.index"))


@activities_bp.route("/<int:activity_id>/delete", methods=["POST"])
@login_required
@household_required
def delete(activity_id):
    activity = Activity.query.filter_by(id=activity_id, household_id=current_user.household_id).first_or_404()
    db.session.delete(activity)
    db.session.commit()
    flash("Atividade eliminada.", "info")
    return redirect(url_for("activities.index"))
