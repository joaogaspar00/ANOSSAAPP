from flask import Blueprint
activities_bp = Blueprint("activities", __name__)
from app.blueprints.activities import routes  # noqa
