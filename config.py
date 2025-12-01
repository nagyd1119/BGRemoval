import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DB_NAME = "bg_app.db"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(INSTANCE_DIR, DB_NAME).replace("\\", "/")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    ORIGINAL_FOLDER = os.path.join(UPLOAD_FOLDER, "original")
    CUTOUT_FOLDER = os.path.join(UPLOAD_FOLDER, "cutout")
    BACKGROUND_FOLDER = os.path.join(UPLOAD_FOLDER, "backgrounds")
    COMPOSED_FOLDER = os.path.join(UPLOAD_FOLDER, "composed")

    @classmethod
    def ensure_dirs(cls):
        for p in [
            cls.UPLOAD_FOLDER,
            cls.ORIGINAL_FOLDER,
            cls.CUTOUT_FOLDER,
            cls.BACKGROUND_FOLDER,
            cls.COMPOSED_FOLDER,
        ]:
            os.makedirs(p, exist_ok=True)
