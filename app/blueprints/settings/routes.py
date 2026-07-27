from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.settings import settings_bp
from app.blueprints.settings.forms import EditProfileForm, ChangePasswordForm, HouseholdForm
from app.models import User, Household
from app.extensions import db, bcrypt
from app.services.price_service import refresh_ingredient_prices
from app.utils import household_required


@settings_bp.route("/")
@login_required
@household_required
def index():
    household = current_user.household
    users = household.members()
    profile_form = EditProfileForm(obj=current_user)
    password_form = ChangePasswordForm()
    household_form = HouseholdForm(obj=household)
    invite_url = url_for("auth.accept_invite", token=household.invite_token, _external=True)
    return render_template(
        "settings/index.html",
        household=household,
        users=users,
        profile_form=profile_form,
        password_form=password_form,
        household_form=household_form,
        invite_url=invite_url,
    )


@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.display_name = form.display_name.data
        current_user.color = form.color.data
        current_user.bio = form.bio.data or None
        db.session.commit()
        flash("Perfil atualizado.", "success")
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
@household_required
def update_household():
    form = HouseholdForm()
    if form.validate_on_submit():
        household = current_user.household
        household.name = form.name.data
        household.currency = form.currency.data
        db.session.commit()
        flash("Definições do casal atualizadas.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/invite/regenerate", methods=["POST"])
@login_required
@household_required
def regenerate_invite():
    household = current_user.household
    household.regenerate_invite()
    db.session.commit()
    flash("Novo link de convite gerado.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/invite/deactivate", methods=["POST"])
@login_required
@household_required
def deactivate_invite():
    household = current_user.household
    household.invite_active = False
    db.session.commit()
    flash("Convite desativado.", "info")
    return redirect(url_for("settings.index"))


@settings_bp.route("/refresh-prices", methods=["POST"])
@login_required
def refresh_prices():
    count = refresh_ingredient_prices(db)
    flash(f"Preços atualizados para {count} ingredientes.", "success")
    return redirect(url_for("settings.index"))
