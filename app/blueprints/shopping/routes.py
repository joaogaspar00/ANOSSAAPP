from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.blueprints.shopping import shopping_bp
from app.models import ShoppingItem
from app.extensions import db
from app.services.shopping_service import sync_shopping_list
from app.utils import household_required


@shopping_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    items = ShoppingItem.query.filter_by(household_id=household_id).order_by(
        ShoppingItem.checked, ShoppingItem.category, ShoppingItem.name
    ).all()

    # Group by category, unchecked first
    grouped: dict[str, list] = {}
    for item in items:
        cat = item.category or "Outro"
        grouped.setdefault(cat, []).append(item)

    total_est = sum(
        (i.estimated_cost or 0) for i in items if not i.checked
    )
    checked_count = sum(1 for i in items if i.checked)
    return render_template(
        "shopping/index.html",
        grouped=grouped,
        total_est=total_est,
        checked_count=checked_count,
        total_count=len(items),
    )


@shopping_bp.route("/generate", methods=["POST"])
@login_required
@household_required
def generate():
    count = sync_shopping_list(current_user.household_id, days_ahead=7)
    flash(f"Lista de compras gerada — {count} produtos adicionados.", "success")
    return redirect(url_for("shopping.index"))


@shopping_bp.route("/add", methods=["POST"])
@login_required
@household_required
def add_manual():
    name = request.form.get("name", "").strip()
    quantity = request.form.get("quantity", 1)
    unit = request.form.get("unit", "").strip()
    category = request.form.get("category", "Outro").strip()

    if not name:
        flash("O nome é obrigatório.", "danger")
        return redirect(url_for("shopping.index"))

    try:
        quantity = float(quantity)
    except ValueError:
        quantity = 1.0

    item = ShoppingItem(
        household_id=current_user.household_id,
        name=name,
        quantity=quantity,
        unit=unit or None,
        category=category,
        source="manual",
    )
    db.session.add(item)
    db.session.commit()
    flash("Produto adicionado.", "success")
    return redirect(url_for("shopping.index"))


@shopping_bp.route("/<int:item_id>/toggle", methods=["POST"])
@login_required
@household_required
def toggle(item_id):
    item = ShoppingItem.query.filter_by(
        id=item_id, household_id=current_user.household_id
    ).first_or_404()
    item.checked = not item.checked
    db.session.commit()
    return redirect(url_for("shopping.index"))


@shopping_bp.route("/clear-checked", methods=["POST"])
@login_required
@household_required
def clear_checked():
    ShoppingItem.query.filter_by(
        household_id=current_user.household_id, checked=True
    ).delete()
    db.session.commit()
    flash("Produtos verificados removidos.", "info")
    return redirect(url_for("shopping.index"))


@shopping_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
@household_required
def delete(item_id):
    item = ShoppingItem.query.filter_by(
        id=item_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("shopping.index"))
