from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

# ---------- N:M kapcsolótábla: users <-> compositions (likes) ----------

user_likes = db.Table(
    "user_likes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("composition_id", db.Integer, db.ForeignKey("compositions.id"), primary_key=True),
)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # profilkép (1:1 egy Compositionnel)
    profile_image_id = db.Column(db.Integer, db.ForeignKey("compositions.id"))
    profile_image = db.relationship(
        "Composition",
        foreign_keys=[profile_image_id],
        uselist=False,
    )

    # 1:N relációk
    images = db.relationship("Image", backref="user", lazy=True)
    comments = db.relationship("Comment", backref="user", lazy=True)

    # N:M – user által kedvelt kompozíciók
    liked_compositions = db.relationship(
        "Composition",
        secondary=user_likes,
        back_populates="likers",
    )

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)


class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    original_path = db.Column(db.String(255), nullable=False)
    cutout_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    compositions = db.relationship("Composition", backref="image", lazy=True)


class Background(db.Model):
    __tablename__ = "backgrounds"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    bg_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    compositions = db.relationship("Composition", backref="background", lazy=True)


class Composition(db.Model):
    __tablename__ = "compositions"

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"), nullable=False)
    background_id = db.Column(db.Integer, db.ForeignKey("backgrounds.id"))
    output_path = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    comments = db.relationship("Comment", backref="composition", lazy=True)

    # N:M – kik kedvelték ezt a kompozíciót
    likers = db.relationship(
        "User",
        secondary=user_likes,
        back_populates="liked_compositions",
    )


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    composition_id = db.Column(db.Integer, db.ForeignKey("compositions.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
