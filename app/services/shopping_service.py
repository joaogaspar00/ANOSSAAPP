"""
services/shopping_service.py — Shopping List Generator

Generates shopping list items from three sources:
  1. Planned meals (recipe ingredients not in inventory)
  2. Low/missing inventory items
  3. Recurring household items

Architecture note:
  This service is stateless — it reads the DB and returns what *should*
  be on the shopping list. It does NOT persist items itself; the caller
  decides whether to save them (to avoid duplicate generation).
"""
from datetime import date, timedelta
from app.extensions import db
from app.models import (
    MealPlan, InventoryItem, ShoppingItem, RecipeIngredient, Ingredient
)
from app.services.price_service import get_price_service
import logging

logger = logging.getLogger(__name__)


def generate_shopping_list(household_id: int, days_ahead: int = 7) -> list[dict]:
    """
    Generate a consolidated shopping list for the household.

    Returns a list of dicts (not yet saved to DB):
    [
      {
        "name": str,
        "quantity": float,
        "unit": str,
        "category": str,
        "source": str,        # "meal_plan" | "inventory" | "recurring"
        "estimated_cost": float | None,
        "ingredient_id": int | None,
      },
      ...
    ]
    """
    items: dict[str, dict] = {}  # keyed by (name.lower(), unit) for dedup

    _add_meal_plan_items(household_id, days_ahead, items)
    _add_inventory_items(household_id, items)

    price_svc = get_price_service()
    result = []
    for item in items.values():
        if item.get("estimated_cost") is None:
            price = price_svc.get_price(item["name"])
            if price:
                item["estimated_cost"] = price * item["quantity"]
        result.append(item)

    # Sort by category then name
    result.sort(key=lambda x: (x.get("category") or "Z", x["name"]))
    logger.info(f"ShoppingService: generated {len(result)} items for household {household_id}")
    return result


def _add_meal_plan_items(household_id: int, days_ahead: int, items: dict):
    """Add ingredients needed for planned meals (that aren't in inventory)."""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    meal_plans = MealPlan.query.filter(
        MealPlan.household_id == household_id,
        MealPlan.planned_date >= today,
        MealPlan.planned_date <= end_date,
        MealPlan.completed == False,
    ).all()

    # Build inventory lookup: name.lower() → quantity
    inv_lookup: dict[str, float] = {}
    for inv in InventoryItem.query.filter_by(household_id=household_id).all():
        inv_lookup[inv.name.lower()] = inv.quantity

    for meal in meal_plans:
        if not meal.recipe:
            continue
        scale = (meal.servings_planned or 2) / max(meal.recipe.servings, 1)
        for ri in meal.recipe.recipe_ingredients:
            needed_qty = ri.quantity * scale
            in_stock = inv_lookup.get(ri.ingredient.name.lower(), 0)
            gap = needed_qty - in_stock
            if gap <= 0:
                continue
            key = (ri.ingredient.name.lower(), ri.unit)
            if key in items:
                items[key]["quantity"] += gap
            else:
                items[key] = {
                    "name": ri.ingredient.name,
                    "quantity": round(gap, 2),
                    "unit": ri.unit,
                    "category": ri.ingredient.category or "Outro",
                    "source": "meal_plan",
                    "estimated_cost": None,
                    "ingredient_id": ri.ingredient_id,
                }


def _add_inventory_items(household_id: int, items: dict):
    """Add items that are low or recurring."""
    for inv in InventoryItem.query.filter_by(household_id=household_id).all():
        should_add = inv.is_recurring or inv.is_low
        if not should_add:
            continue
        source = "recurring" if inv.is_recurring else "inventory"
        needed = 0.0
        if inv.min_threshold and inv.quantity < inv.min_threshold:
            needed = inv.min_threshold - inv.quantity
        elif inv.is_recurring:
            needed = inv.min_threshold or 1.0

        key = (inv.name.lower(), inv.unit)
        if key not in items:
            items[key] = {
                "name": inv.name,
                "quantity": round(needed, 2),
                "unit": inv.unit,
                "category": inv.category or "Outro",
                "source": source,
                "estimated_cost": None,
                "ingredient_id": inv.ingredient_id,
            }


def sync_shopping_list(household_id: int, days_ahead: int = 7):
    """
    Regenerates the shopping list in the DB.
    Removes auto-generated unchecked items, then re-adds from current state.
    Manual items (source='manual') and checked items are preserved.
    """
    # Remove old auto-generated unchecked items
    ShoppingItem.query.filter(
        ShoppingItem.household_id == household_id,
        ShoppingItem.source != "manual",
        ShoppingItem.checked == False,
    ).delete()
    db.session.flush()

    generated = generate_shopping_list(household_id, days_ahead)
    for g in generated:
        item = ShoppingItem(
            household_id=household_id,
            ingredient_id=g.get("ingredient_id"),
            name=g["name"],
            quantity=g["quantity"],
            unit=g.get("unit"),
            category=g.get("category"),
            source=g["source"],
            estimated_cost=g.get("estimated_cost"),
        )
        db.session.add(item)

    db.session.commit()
    return len(generated)
