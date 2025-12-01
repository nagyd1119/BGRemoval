from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# 1) Itt hozzuk létre a db-t, még függvényen kívül
db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    Config.ensure_dirs()

    # 2) db inicializálása
    db.init_app(app)

    # 3) modellek importja, amikor már van app + db
    with app.app_context():
        from . import models  # <- CSAK ITT legyen ilyen import
        db.create_all()

    # 4) blueprint-ek
    from .auth.routes import auth_bp
    from .gallery.routes import gallery_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(gallery_bp)

    @app.route("/ping")
    def ping():
        return "OK"

    return app
