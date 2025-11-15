from flask import Blueprint, Flask

from .health_routes import health_bp
from .library_routes import library_bp
from .match_routes import match_bp
from .personality_routes import personality_bp
from .search_routes import search_bp
from .spotify_routes import spotify_bp
from .users_routes import users_bp
from .register_routes import register_routes
from .debug_routes import debug_bp
from .library_routes import library_bp
# def register_routes(app: Flask) -> None:
#     blueprints: list[Blueprint] = [
#         health_bp,
#         users_bp,
#         match_bp,
#         library_bp,
#         search_bp,
#         personality_bp,
#         spotify_bp,
#     ]

#     for blueprint in blueprints:
#         app.register_blueprint(blueprint, url_prefix="/api")

def register_routes(app: Flask) -> None:
    app.register_blueprint(health_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(library_bp)