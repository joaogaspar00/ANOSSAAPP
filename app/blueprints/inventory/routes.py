from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.inventory import inventory_bp
from app.blueprints.inventory.forms import InventoryItemForm, AdjustQuantityForm
from app.models import InventoryItem
from app.extensions import db
from app.utils import household_required


@inventory_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    items = InventoryItem.query.filter_by(household_id=household_id).order_by(
        InventoryItem.category, InventoryItem.name
    ).all()

    # Group by category
    grouped: dict[str, list] = {}
    for item in items:
        cat = item.category or "Outro"
        grouped.setdefault(cat, []).append(item)

    low_count = sum(1 for i in items if i.is_low)
    form = InventoryItemForm()
    return render_template("inventory/index.html", grouped=grouped, low_count=low_count, form=form)


@inventory_bp.route("/add", methods=["GET", "POST"])
@login_required
@household_required
def add():
    form = InventoryItemForm()
    if form.validate_on_submit():
        item = InventoryItem(
            household_id=current_user.household_id,
            name=form.name.data,
            quantity=form.quantity.data,
            unit=form.unit.data,
            min_threshold=form.min_threshold.data,
            is_recurring=form.is_recurring.data,
            category=form.category.data,
        )
        db.session.add(item)
        db.session.commit()
        flash("Produto adicionado à despensa.", "success")
        return redirect(url_for("inventory.index"))
    return render_template("inventory/form.html", form=form, editing=False)


@inventory_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit(item_id):
    item = InventoryItem.query.filter_by(
        id=item_id, household_id=current_user.household_id
    ).first_or_404()
    form = InventoryItemForm(obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash("Despensa atualizada.", "success")
        return redirect(url_for("inventory.index"))
    return render_template("inventory/form.html", form=form, editing=True, item=item)


@inventory_bp.route("/<int:item_id>/adjust", methods=["POST"])
@login_required
@household_required
def adjust(item_id):
    item = InventoryItem.query.filter_by(
        id=item_id, household_id=current_user.household_id
    ).first_or_404()
    try:
        delta = float(request.form.get("delta", 0))
        item.quantity = max(0, item.quantity + delta)
        db.session.commit()
        flash(f"'{item.name}' atualizado para {item.quantity} {item.unit}.", "success")
    except ValueError:
        flash("Quantidade inválida.", "danger")
    return redirect(url_for("inventory.index"))


@inventory_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
@household_required
def delete(item_id):
    item = InventoryItem.query.filter_by(
        id=item_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Produto removido da despensa.", "info")
    return redirect(url_for("inventory.index"))
