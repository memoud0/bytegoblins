from flask import Flask
from .debug_routes import debug_bp
from .health_routes import health_bp
from .users_routes import users_bp


def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(users_bp)
