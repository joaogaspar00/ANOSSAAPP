from flask import Blueprint
inventory_bp = Blueprint("inventory", __name__)
from app.blueprints.inventory import routes  # noqa
