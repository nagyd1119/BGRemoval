from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    Config.ensure_dirs()

    db.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()

    from .auth.routes import auth_bp
    from .gallery.routes import gallery_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(gallery_bp)

    @app.route("/ping")
    def ping():
        return "OK"

    return app
