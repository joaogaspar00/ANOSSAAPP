from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from app.blueprints.meals import meals_bp
from app.blueprints.meals.forms import RecipeForm, MealPlanForm
from app.models import Recipe, Ingredient, RecipeIngredient, MealPlan, MEAL_SLOTS
from app.extensions import db
from app.services.price_service import get_price_service
from app.utils import household_required


# ── Meal Plan ────────────────────────────────────────────────────────────────

@meals_bp.route("/")
@login_required
@household_required
def index():
    household_id = current_user.household_id
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    meal_plans = MealPlan.query.filter(
        MealPlan.household_id == household_id,
        MealPlan.planned_date >= week_start,
        MealPlan.planned_date <= week_end,
    ).order_by(MealPlan.planned_date, MealPlan.meal_slot).all()

    # Build week grid: date → slot → meal
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    slots = ["breakfast", "lunch", "dinner", "snack"]
    slot_labels = {"breakfast": "Pequeno-almoço", "lunch": "Almoço", "dinner": "Jantar", "snack": "Lanche"}
    grid = {d: {s: [] for s in slots} for d in week_days}
    for mp in meal_plans:
        if mp.planned_date in grid and mp.meal_slot in grid[mp.planned_date]:
            grid[mp.planned_date][mp.meal_slot].append(mp)

    form = MealPlanForm()
    recipes = Recipe.query.filter_by(household_id=household_id).order_by(Recipe.name).all()
    form.recipe_id.choices = [(0, "— sem receita —")] + [(r.id, r.name) for r in recipes]

    return render_template(
        "meals/index.html",
        grid=grid,
        week_days=week_days,
        slots=slots,
        slot_labels=slot_labels,
        form=form,
        today=today,
    )


@meals_bp.route("/plan/add", methods=["POST"])
@login_required
@household_required
def add_plan():
    household_id = current_user.household_id
    form = MealPlanForm()
    recipes = Recipe.query.filter_by(household_id=household_id).all()
    form.recipe_id.choices = [(0, "— sem receita —")] + [(r.id, r.name) for r in recipes]

    if form.validate_on_submit():
        mp = MealPlan(
            household_id=household_id,
            planned_date=form.planned_date.data,
            meal_slot=form.meal_slot.data,
            recipe_id=form.recipe_id.data or None,
            custom_name=form.custom_name.data or None,
            servings_planned=form.servings_planned.data or 2,
            notes=form.notes.data or None,
        )
        db.session.add(mp)
        db.session.commit()
        flash("Refeição planeada.", "success")
    return redirect(url_for("meals.index"))


@meals_bp.route("/plan/<int:plan_id>/complete", methods=["POST"])
@login_required
@household_required
def complete_plan(plan_id):
    mp = MealPlan.query.filter_by(id=plan_id, household_id=current_user.household_id).first_or_404()
    mp.completed = True
    # Optionally decrease inventory here in future
    db.session.commit()
    flash("Refeição marcada como consumida!", "success")
    return redirect(url_for("meals.index"))


@meals_bp.route("/plan/<int:plan_id>/delete", methods=["POST"])
@login_required
@household_required
def delete_plan(plan_id):
    mp = MealPlan.query.filter_by(id=plan_id, household_id=current_user.household_id).first_or_404()
    db.session.delete(mp)
    db.session.commit()
    flash("Refeição removida.", "info")
    return redirect(url_for("meals.index"))


# ── Recipes ──────────────────────────────────────────────────────────────────

@meals_bp.route("/recipes")
@login_required
@household_required
def recipes():
    all_recipes = Recipe.query.filter_by(
        household_id=current_user.household_id
    ).order_by(Recipe.name).all()
    return render_template("meals/recipes.html", recipes=all_recipes)


@meals_bp.route("/recipes/add", methods=["GET", "POST"])
@login_required
@household_required
def add_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        recipe = Recipe(
            household_id=current_user.household_id,
            name=form.name.data,
            servings=form.servings.data,
            prep_time_minutes=form.prep_time_minutes.data,
            category=form.category.data or None,
            instructions=form.instructions.data or None,
        )
        db.session.add(recipe)
        db.session.flush()

        # Parse ingredients from request (dynamic rows)
        _save_recipe_ingredients(recipe, request)
        db.session.commit()
        flash("Receita guardada.", "success")
        return redirect(url_for("meals.recipes"))
    return render_template("meals/recipe_form.html", form=form, recipe=None)


@meals_bp.route("/recipes/<int:recipe_id>")
@login_required
@household_required
def view_recipe(recipe_id):
    recipe = Recipe.query.filter_by(
        id=recipe_id, household_id=current_user.household_id
    ).first_or_404()
    return render_template("meals/recipe_detail.html", recipe=recipe)


@meals_bp.route("/recipes/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
@household_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.filter_by(
        id=recipe_id, household_id=current_user.household_id
    ).first_or_404()
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        recipe.name = form.name.data
        recipe.servings = form.servings.data
        recipe.prep_time_minutes = form.prep_time_minutes.data
        recipe.category = form.category.data or None
        recipe.instructions = form.instructions.data or None
        # Remove old ingredients and re-save
        for ri in recipe.recipe_ingredients:
            db.session.delete(ri)
        db.session.flush()
        _save_recipe_ingredients(recipe, request)
        db.session.commit()
        flash("Receita atualizada.", "success")
        return redirect(url_for("meals.view_recipe", recipe_id=recipe.id))
    return render_template("meals/recipe_form.html", form=form, recipe=recipe)


@meals_bp.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
@login_required
@household_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.filter_by(
        id=recipe_id, household_id=current_user.household_id
    ).first_or_404()
    db.session.delete(recipe)
    db.session.commit()
    flash("Receita eliminada.", "info")
    return redirect(url_for("meals.recipes"))


def _save_recipe_ingredients(recipe, req):
    """Parse ingredient rows from form POST and create RecipeIngredient records."""
    price_svc = get_price_service()
    names = req.form.getlist("ing_name")
    quantities = req.form.getlist("ing_quantity")
    units = req.form.getlist("ing_unit")

    for name, qty_str, unit in zip(names, quantities, units):
        name = name.strip()
        if not name:
            continue
        try:
            qty = float(qty_str)
        except (ValueError, TypeError):
            qty = 1.0

        # Get or create ingredient
        ingredient = Ingredient.query.filter_by(name=name).first()
        if not ingredient:
            price = price_svc.get_price(name)
            ingredient = Ingredient(
                name=name,
                default_unit=unit or None,
                price_per_unit=price,
                category=None,
            )
            db.session.add(ingredient)
            db.session.flush()

        ri = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.id,
            quantity=qty,
            unit=unit or ingredient.default_unit or "un",
        )
        db.session.add(ri)
