from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.settings import settings_bp
from app.blueprints.settings.forms import EditProfileForm, ChangePasswordForm, HouseholdNameForm
from app.models import User, Household
from app.extensions import db, bcrypt
from app.services.price_service import refresh_ingredient_prices


@settings_bp.route("/")
@login_required
def index():
    household = Household.query.get(current_user.household_id)
    users = User.query.filter_by(household_id=current_user.household_id).all()
    profile_form = EditProfileForm(obj=current_user)
    password_form = ChangePasswordForm()
    household_form = HouseholdNameForm(obj=household)
    return render_template(
        "settings/index.html",
        household=household,
        users=users,
        profile_form=profile_form,
        password_form=password_form,
        household_form=household_form,
    )


@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        db.session.commit()
        flash("Nome atualizado.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = bcrypt.generate_password_hash(
                form.new_password.data
            ).decode("utf-8")
            db.session.commit()
            flash("Palavra-passe alterada.", "success")
        else:
            flash("Palavra-passe atual incorreta.", "danger")
    return redirect(url_for("settings.index"))


@settings_bp.route("/household", methods=["POST"])
@login_required
def update_household():
    form = HouseholdNameForm()
    if form.validate_on_submit():
        household = Household.query.get(current_user.household_id)
        household.name = form.name.data
        db.session.commit()
        flash("Nome do agregado familiar atualizado.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/refresh-prices", methods=["POST"])
@login_required
def refresh_prices():
    count = refresh_ingredient_prices(db)
    flash(f"Preços atualizados para {count} ingredientes.", "success")
    return redirect(url_for("settings.index"))
