"""
models.py — SQLAlchemy ORM models

Design notes:
- Household is the root aggregate; all data belongs to it.
- Two users share one household; no per-user financial data.
- All monetary values in DKK (stored as Float, displayed formatted).
- RecurrenceRule is a separate table so task scheduling stays flexible.
"""
from datetime import datetime, date
from app.extensions import db, login_manager
from flask_login import UserMixin


# ---------------------------------------------------------------------------
# User loader required by Flask-Login
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Household — the single shared root entity
# ---------------------------------------------------------------------------
class Household(db.Model):
    __tablename__ = "household"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="Vores Hjem")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship("User", back_populates="household", lazy="select")
    expenses = db.relationship("Expense", back_populates="household", lazy="dynamic")
    tasks = db.relationship("Task", back_populates="household", lazy="dynamic")
    calendar_events = db.relationship("CalendarEvent", back_populates="household", lazy="dynamic")
    recipes = db.relationship("Recipe", back_populates="household", lazy="dynamic")
    inventory_items = db.relationship("InventoryItem", back_populates="household", lazy="dynamic")
    shopping_items = db.relationship("ShoppingItem", back_populates="household", lazy="dynamic")
    meal_plans = db.relationship("MealPlan", back_populates="household", lazy="dynamic")

    def __repr__(self):
        return f"<Household {self.name}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="users")
    assigned_tasks = db.relationship("Task", back_populates="assigned_to", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------------------------------------------------------------------
# Finance — Expense
# ---------------------------------------------------------------------------
EXPENSE_CATEGORIES = [
    "Alimentação",
    "Casa",
    "Transporte",
    "Saúde",
    "Entretenimento",
    "Habitação",
    "Vestuário",
    "Outro",
]


class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # DKK
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="expenses")

    def __repr__(self):
        return f"<Expense {self.amount} DKK — {self.category}>"


# ---------------------------------------------------------------------------
# Tasks & Recurrence
# ---------------------------------------------------------------------------
RECURRENCE_TYPES = ["none", "daily", "weekly", "every_x_days", "monthly"]


class RecurrenceRule(db.Model):
    __tablename__ = "recurrence_rule"

    id = db.Column(db.Integer, primary_key=True)
    rule_type = db.Column(db.String(32), nullable=False, default="none")
    interval_days = db.Column(db.Integer, nullable=True)  # used for every_x_days
    tasks = db.relationship("Task", back_populates="recurrence_rule", lazy="select")

    def __repr__(self):
        return f"<RecurrenceRule {self.rule_type}>"


class Task(db.Model):
    __tablename__ = "task"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    recurrence_rule_id = db.Column(db.Integer, db.ForeignKey("recurrence_rule.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="tasks")
    assigned_to = db.relationship("User", back_populates="assigned_tasks")
    recurrence_rule = db.relationship("RecurrenceRule", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.title}>"


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
EVENT_TYPES = ["task", "meal", "shopping", "external"]


class CalendarEvent(db.Model):
    __tablename__ = "calendar_event"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(32), nullable=False, default="external")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    start_time = db.Column(db.Time, nullable=True)
    all_day = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    # Link to source entity (optional)
    source_task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=True)
    source_meal_plan_id = db.Column(db.Integer, db.ForeignKey("meal_plan.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="calendar_events")

    def __repr__(self):
        return f"<CalendarEvent {self.title} on {self.start_date}>"


# ---------------------------------------------------------------------------
# Recipes & Ingredients
# ---------------------------------------------------------------------------
class Recipe(db.Model):
    __tablename__ = "recipe"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    servings = db.Column(db.Integer, nullable=False, default=2)
    prep_time_minutes = db.Column(db.Integer, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(64), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="recipes")
    recipe_ingredients = db.relationship(
        "RecipeIngredient", back_populates="recipe",
        cascade="all, delete-orphan", lazy="select"
    )
    meal_plans = db.relationship("MealPlan", back_populates="recipe", lazy="dynamic")

    @property
    def total_cost(self):
        """Sum of all ingredient costs in DKK."""
        return sum(ri.line_cost for ri in self.recipe_ingredients)

    @property
    def cost_per_serving(self):
        if self.servings and self.servings > 0:
            return self.total_cost / self.servings
        return 0.0

    def __repr__(self):
        return f"<Recipe {self.name}>"


class Ingredient(db.Model):
    """
    Master ingredient catalogue with reference price from Danish market.
    PriceService populates/updates price_dkk_per_unit.
    """
    __tablename__ = "ingredient"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    default_unit = db.Column(db.String(32), nullable=True)
    price_dkk_per_unit = db.Column(db.Float, nullable=True)  # cached from PriceService
    price_updated_at = db.Column(db.DateTime, nullable=True)
    category = db.Column(db.String(64), nullable=True)  # for shopping list grouping

    recipe_usages = db.relationship("RecipeIngredient", back_populates="ingredient", lazy="dynamic")

    def __repr__(self):
        return f"<Ingredient {self.name}>"


class RecipeIngredient(db.Model):
    """Join table between Recipe and Ingredient with quantity + unit."""
    __tablename__ = "recipe_ingredient"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32), nullable=False)

    recipe = db.relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = db.relationship("Ingredient", back_populates="recipe_usages")

    @property
    def line_cost(self):
        """Cost for this ingredient line in DKK."""
        if self.ingredient and self.ingredient.price_dkk_per_unit:
            return self.quantity * self.ingredient.price_dkk_per_unit
        return 0.0

    def __repr__(self):
        return f"<RecipeIngredient {self.quantity}{self.unit} {self.ingredient.name if self.ingredient else '?'}>"


# ---------------------------------------------------------------------------
# Meal Plan
# ---------------------------------------------------------------------------
MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"]


class MealPlan(db.Model):
    __tablename__ = "meal_plan"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipe.id"), nullable=True)
    planned_date = db.Column(db.Date, nullable=False)
    meal_slot = db.Column(db.String(32), nullable=False, default="dinner")
    custom_name = db.Column(db.String(200), nullable=True)  # for no-recipe meals
    servings_planned = db.Column(db.Integer, default=2)
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    household = db.relationship("Household", back_populates="meal_plans")
    recipe = db.relationship("Recipe", back_populates="meal_plans")

    @property
    def display_name(self):
        if self.recipe:
            return self.recipe.name
        return self.custom_name or "Refeição sem nome"

    def __repr__(self):
        return f"<MealPlan {self.display_name} on {self.planned_date}>"


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
class InventoryItem(db.Model):
    __tablename__ = "inventory_item"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0)
    unit = db.Column(db.String(32), nullable=False)
    min_threshold = db.Column(db.Float, nullable=True)  # alert when below this
    is_recurring = db.Column(db.Boolean, default=False)  # always on shopping list
    category = db.Column(db.String(64), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    household = db.relationship("Household", back_populates="inventory_items")
    ingredient = db.relationship("Ingredient")

    @property
    def is_low(self):
        if self.min_threshold is not None:
            return self.quantity <= self.min_threshold
        return False

    def __repr__(self):
        return f"<InventoryItem {self.name} {self.quantity}{self.unit}>"


# ---------------------------------------------------------------------------
# Shopping List
# ---------------------------------------------------------------------------
SHOPPING_SOURCES = ["meal_plan", "inventory", "recurring", "manual"]


class ShoppingItem(db.Model):
    __tablename__ = "shopping_item"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredient.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit = db.Column(db.String(32), nullable=True)
    category = db.Column(db.String(64), nullable=True)
    source = db.Column(db.String(32), nullable=False, default="manual")
    checked = db.Column(db.Boolean, default=False)
    estimated_cost = db.Column(db.Float, nullable=True)  # DKK
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="shopping_items")
    ingredient = db.relationship("Ingredient")

    def __repr__(self):
        return f"<ShoppingItem {self.name}>"
