from flask import Blueprint
goals_bp = Blueprint("goals", __name__)
from app.blueprints.goals import routes  # noqa
