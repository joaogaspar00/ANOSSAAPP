from flask import Flask, render_template
from config import config
from app.extensions import db, login_manager, bcrypt, csrf, migrate


def create_app(config_name="default"):
    app = Flask(__name__)
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
    from app.blueprints.goals import goals_bp
    from app.blueprints.activities import activities_bp
    from app.blueprints.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(finance_bp, url_prefix="/finance")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(meals_bp, url_prefix="/meals")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(shopping_bp, url_prefix="/shopping")
    app.register_blueprint(goals_bp, url_prefix="/goals")
    app.register_blueprint(activities_bp, url_prefix="/activities")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    _register_error_handlers(app)

    return app


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template(
            "errors/error.html", code=404, title="Página não encontrada",
            message="A página que procuras não existe ou foi movida.",
        ), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template(
            "errors/error.html", code=403, title="Acesso negado",
            message="Não tens permissão para aceder a esta página.",
        ), 403

    @app.errorhandler(500)
    def server_error(e):
        return render_template(
            "errors/error.html", code=500, title="Erro no servidor",
            message="Algo correu mal. Tenta novamente dentro de instantes.",
        ), 500
