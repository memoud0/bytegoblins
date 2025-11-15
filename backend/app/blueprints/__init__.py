from flask import Blueprint, Flask

from .health import health_bp
from .spotify import spotify_bp


def register_blueprints(app: Flask) -> None:
    blueprints: list[Blueprint] = [
        health_bp,
        spotify_bp,
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint, url_prefix="/api")
