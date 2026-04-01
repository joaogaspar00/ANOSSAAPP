from flask import Blueprint
shopping_bp = Blueprint("shopping", __name__)
from app.blueprints.shopping import routes  # noqa
