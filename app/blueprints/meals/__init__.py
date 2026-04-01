from flask import Blueprint
meals_bp = Blueprint("meals", __name__)
from app.blueprints.meals import routes  # noqa
