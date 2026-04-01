from flask import Blueprint
shopping_bp = Blueprint("shopping", __name__)
from app.blueprints.shopping import routes  # noqa
from flask import Flask
from config import config
from app.extensions import db, login_manager, bcrypt, csrf, migrate


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.finance import finance_bp
    from app.blueprints.tasks import tasks_bp
    from app.blueprints.calendar import calendar_bp
    from app.blueprints.meals import meals_bp
    from app.blueprints.inventory import inventory_bp
    from app.blueprints.shopping import shopping_bp
    from app.blueprints.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(finance_bp, url_prefix="/finance")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(meals_bp, url_prefix="/meals")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(shopping_bp, url_prefix="/shopping")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    with app.app_context():
        db.create_all()
        _seed_initial_data()

    return app


def _seed_initial_data():
    from app.models import Household, User
    from app.extensions import bcrypt as _bcrypt

    if Household.query.first():
        return

    household = Household(name="A Nossa Casa")
    db.session.add(household)
    db.session.flush()

    users = [
        User(
            household_id=household.id,
            username="user1",
            display_name="Person 1",
            password_hash=_bcrypt.generate_password_hash("changeme1").decode("utf-8"),
        ),
        User(
            household_id=household.id,
            username="user2",
            display_name="Person 2",
            password_hash=_bcrypt.generate_password_hash("changeme2").decode("utf-8"),
        ),
    ]
    db.session.add_all(users)
    db.session.commit()