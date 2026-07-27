from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm, RegisterForm, HouseholdForm
from app.models import User, Household
from app.extensions import db, bcrypt


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Nome de utilizador ou palavra-passe incorretos.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def _pending_invite():
    """Resolve an invite token from the query string or session into an open Household."""
    token = request.args.get("convite") or session.get("invite_token")
    if not token:
        return None
    household = Household.query.filter_by(invite_token=token, invite_active=True).first()
    if not household or household.is_complete():
        return None
    session["invite_token"] = token
    return household


@auth_bp.route("/registar", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    invite_household = _pending_invite()
    form = RegisterForm()

    if form.validate_on_submit():
        user = User(
            display_name=form.display_name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            password_hash=bcrypt.generate_password_hash(form.password.data).decode("utf-8"),
        )

        token = session.get("invite_token")
        household = Household.query.filter_by(invite_token=token, invite_active=True).first() if token else None
        if household and household.is_complete():
            household = None
        if household:
            user.household_id = household.id

        db.session.add(user)
        db.session.flush()

        if household:
            if household.is_complete():
                household.invite_active = False
            session.pop("invite_token", None)
            db.session.commit()
            login_user(user, remember=True)
            flash(f"Bem-vindo ao casal {household.name}!", "success")
            return redirect(url_for("dashboard.index"))

        db.session.commit()
        login_user(user, remember=True)
        flash("Conta criada! Configura o teu casal.", "success")
        return redirect(url_for("auth.onboarding"))

    return render_template("auth/register.html", form=form, invite_household=invite_household)


@auth_bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    if current_user.household_id:
        return redirect(url_for("dashboard.index"))
    form = HouseholdForm()
    if form.validate_on_submit():
        household = Household(name=form.name.data.strip(), currency=form.currency.data)
        db.session.add(household)
        db.session.flush()
        current_user.household_id = household.id
        db.session.commit()
        flash(f'Casal "{household.name}" criado! Partilha o convite com o teu parceiro.', "success")
        return redirect(url_for("dashboard.index"))
    return render_template("auth/onboarding.html", form=form)


@auth_bp.route("/convite/<token>")
def accept_invite(token):
    household = Household.query.filter_by(invite_token=token, invite_active=True).first_or_404()
    if household.is_complete():
        flash("Este convite já não está disponível — o casal está completo.", "danger")
        return redirect(url_for("auth.login"))

    if current_user.is_authenticated:
        if current_user.household_id:
            flash("Já pertences a um casal.", "warning")
            return redirect(url_for("dashboard.index"))
        current_user.household_id = household.id
        if household.is_complete():
            household.invite_active = False
        db.session.commit()
        flash(f"Juntaste-te ao casal {household.name}!", "success")
        return redirect(url_for("dashboard.index"))

    session["invite_token"] = token
    flash(f'Regista-te para te juntares ao casal "{household.name}".', "info")
    return redirect(url_for("auth.register", convite=token))
