"""
models.py — SQLAlchemy ORM models

Design notes:
- Household is the root aggregate; all data belongs to it.
- Two users share one household; no per-user financial data.
- Monetary values stored as Float in the household's currency.
- RecurrenceRule is a separate table so task scheduling stays flexible.
"""
import uuid
from datetime import datetime, date
from app.extensions import db, login_manager
from flask_login import UserMixin


# ---------------------------------------------------------------------------
# User loader required by Flask-Login
# ---------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


CURRENCY_SYMBOLS = {
    "DKK": "kr", "EUR": "€", "USD": "$", "GBP": "£", "SEK": "kr", "NOK": "kr",
}


# ---------------------------------------------------------------------------
# Household — the single shared root entity
# ---------------------------------------------------------------------------
class Household(db.Model):
    __tablename__ = "household"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default="A Nossa Casa")
    currency = db.Column(db.String(10), nullable=False, default="EUR")
    invite_token = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    invite_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship("User", back_populates="household", lazy="select")
    expenses = db.relationship("Expense", back_populates="household", lazy="dynamic")
    settlements = db.relationship("Settlement", back_populates="household", lazy="dynamic")
    tasks = db.relationship("Task", back_populates="household", lazy="dynamic")
    calendar_events = db.relationship("CalendarEvent", back_populates="household", lazy="dynamic")
    recipes = db.relationship("Recipe", back_populates="household", lazy="dynamic")
    inventory_items = db.relationship("InventoryItem", back_populates="household", lazy="dynamic")
    shopping_items = db.relationship("ShoppingItem", back_populates="household", lazy="dynamic")
    meal_plans = db.relationship("MealPlan", back_populates="household", lazy="dynamic")
    goals = db.relationship("Goal", back_populates="household", lazy="dynamic")
    activities = db.relationship("Activity", back_populates="household", lazy="dynamic")

    def members(self):
        return User.query.filter_by(household_id=self.id).order_by(User.id).all()

    def partner(self, user):
        return User.query.filter(
            User.household_id == self.id, User.id != user.id
        ).first()

    def is_complete(self):
        return len(self.members()) >= 2

    def currency_symbol(self):
        return CURRENCY_SYMBOLS.get(self.currency, self.currency)

    def regenerate_invite(self):
        self.invite_token = str(uuid.uuid4())
        self.invite_active = True

    def __repr__(self):
        return f"<Household {self.name}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#5C6BC0")
    bio = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="users")
    assigned_tasks = db.relationship("Task", back_populates="assigned_to", lazy="dynamic")

    def initials(self):
        parts = self.display_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.display_name[:2].upper()

    def __repr__(self):
        return f"<User {self.username}>"


# ---------------------------------------------------------------------------
# Finance — Expense & Settlement
# ---------------------------------------------------------------------------
EXPENSE_CATEGORIES = [
    "Alimentação",
    "Casa",
    "Transporte",
    "Saúde",
    "Entretenimento",
    "Habitação",
    "Vestuário",
    "Viagem",
    "Subscrições",
    "Outro",
]

SPLIT_TYPES = [
    ("50_50", "50/50"),
    ("full_me", "Pago por mim (total)"),
    ("full_partner", "Pago pelo parceiro (total)"),
    ("custom", "Personalizado"),
]


class Expense(db.Model):
    __tablename__ = "expense"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    paid_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    category = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    split_type = db.Column(db.String(20), nullable=False, default="50_50")
    amount_a = db.Column(db.Float, nullable=False, default=0)  # share owed by members()[0]
    amount_b = db.Column(db.Float, nullable=False, default=0)  # share owed by members()[1]
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="expenses")
    paid_by = db.relationship("User")

    def compute_split(self):
        household = self.household or Household.query.get(self.household_id)
        members = household.members()
        if len(members) < 2:
            return
        if self.split_type == "50_50":
            half = self.amount / 2
            self.amount_a = half
            self.amount_b = half
        elif self.split_type == "full_me":
            payer_is_a = self.paid_by_id == members[0].id
            self.amount_a = 0 if payer_is_a else self.amount
            self.amount_b = self.amount if payer_is_a else 0
        elif self.split_type == "full_partner":
            payer_is_a = self.paid_by_id == members[0].id
            self.amount_a = self.amount if payer_is_a else 0
            self.amount_b = 0 if payer_is_a else self.amount
        # "custom": amount_a/amount_b are set explicitly by the form

    def __repr__(self):
        return f"<Expense {self.amount} — {self.category}>"


class Settlement(db.Model):
    __tablename__ = "settlement"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="settlements")
    from_user = db.relationship("User", foreign_keys=[from_user_id])
    to_user = db.relationship("User", foreign_keys=[to_user_id])

    def __repr__(self):
        return f"<Settlement {self.from_user_id} -> {self.to_user_id}: {self.amount}>"


# ---------------------------------------------------------------------------
# Tasks & Recurrence
# ---------------------------------------------------------------------------
RECURRENCE_TYPES = ["none", "daily", "weekly", "every_x_days", "monthly"]
TASK_STATUSES = [
    ("pending", "Pendente"),
    ("in_progress", "Em curso"),
    ("done", "Concluída"),
]
TASK_PRIORITIES = [
    ("low", "Baixa"),
    ("medium", "Média"),
    ("high", "Alta"),
]


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
    status = db.Column(db.String(20), nullable=False, default="pending")
    priority = db.Column(db.String(10), nullable=False, default="medium")
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="tasks")
    assigned_to = db.relationship("User", back_populates="assigned_tasks")
    recurrence_rule = db.relationship("RecurrenceRule", back_populates="tasks")

    def is_overdue(self):
        if self.due_date and self.status != "done":
            return self.due_date < date.today()
        return False

    def __repr__(self):
        return f"<Task {self.title}>"


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
EVENT_TYPES = ["task", "meal", "shopping", "external"]
EVENT_VISIBILITIES = [
    ("shared", "Partilhado"),
    ("personal", "Pessoal"),
]


class CalendarEvent(db.Model):
    __tablename__ = "calendar_event"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(32), nullable=False, default="external")
    visibility = db.Column(db.String(20), nullable=False, default="shared")
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
    owner = db.relationship("User")

    def visible_to(self, user):
        if self.visibility == "shared":
            return True
        return self.owner_id == user.id

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
        return sum(ri.line_cost for ri in self.recipe_ingredients)

    @property
    def cost_per_serving(self):
        if self.servings and self.servings > 0:
            return self.total_cost / self.servings
        return 0.0

    def __repr__(self):
        return f"<Recipe {self.name}>"


class Ingredient(db.Model):
    """Master ingredient catalogue with a cached reference price."""
    __tablename__ = "ingredient"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    default_unit = db.Column(db.String(32), nullable=True)
    price_per_unit = db.Column(db.Float, nullable=True)  # cached from PriceService
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
        if self.ingredient and self.ingredient.price_per_unit:
            return self.quantity * self.ingredient.price_per_unit
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
    estimated_cost = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="shopping_items")
    ingredient = db.relationship("Ingredient")

    def __repr__(self):
        return f"<ShoppingItem {self.name}>"


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------
GOAL_TYPES = [
    ("financial", "Financeiro"),
    ("travel", "Viagem"),
    ("home", "Casa"),
    ("personal", "Pessoal"),
    ("other", "Outro"),
]
GOAL_STATUSES = [
    ("active", "Ativo"),
    ("completed", "Concluído"),
    ("paused", "Pausado"),
]


class Goal(db.Model):
    __tablename__ = "goal"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(20), nullable=False, default="other")
    target_value = db.Column(db.Float, nullable=True)
    current_value = db.Column(db.Float, nullable=False, default=0)
    deadline = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    household = db.relationship("Household", back_populates="goals")
    created_by = db.relationship("User")

    def progress_percent(self):
        if not self.target_value:
            return 0
        pct = (self.current_value / self.target_value) * 100
        return min(int(pct), 100)

    def remaining_value(self):
        if not self.target_value:
            return None
        return max(self.target_value - self.current_value, 0)

    def sync_status(self):
        if self.target_value and self.current_value >= self.target_value and self.status == "active":
            self.status = "completed"

    def __repr__(self):
        return f"<Goal {self.title}>"


# ---------------------------------------------------------------------------
# Activities (couple wishlist)
# ---------------------------------------------------------------------------
ACTIVITY_TYPES = [
    ("restaurant", "Restaurante"),
    ("museum", "Museu / Exposição"),
    ("show", "Concerto / Espetáculo"),
    ("travel", "Viagem"),
    ("cinema", "Cinema"),
    ("sport", "Desporto"),
    ("nature", "Natureza / Outdoor"),
    ("other", "Outro"),
]
ACTIVITY_STATUSES = [
    ("wishlist", "Wishlist"),
    ("planned", "Planeado"),
    ("done", "Feito"),
]


class Activity(db.Model):
    __tablename__ = "activity"

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("household.id"), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="other")
    status = db.Column(db.String(20), nullable=False, default="wishlist")
    planned_date = db.Column(db.Date, nullable=True)
    done_date = db.Column(db.Date, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    rating_a = db.Column(db.Integer, nullable=True)  # rating given by members()[0]
    rating_b = db.Column(db.Integer, nullable=True)  # rating given by members()[1]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    household = db.relationship("Household", back_populates="activities")
    created_by = db.relationship("User")

    def average_rating(self):
        ratings = [r for r in (self.rating_a, self.rating_b) if r is not None]
        if not ratings:
            return None
        return sum(ratings) / len(ratings)

    def rating_for(self, user):
        members = self.household.members()
        if not members:
            return None
        return self.rating_a if user.id == members[0].id else self.rating_b

    def set_rating(self, user, value):
        members = self.household.members()
        if not members:
            return
        if user.id == members[0].id:
            self.rating_a = value
        else:
            self.rating_b = value

    def __repr__(self):
        return f"<Activity {self.name}>"
