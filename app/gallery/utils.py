import os
from uuid import uuid4
from PIL import Image
from rembg import remove
from werkzeug.utils import secure_filename
from flask import current_app
from ..models import Image as ImageModel, Background, Composition
from .. import db


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image_file(file_storage, folder: str) -> str:
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    new_name = f"{uuid4().hex}.{ext}"
    path = os.path.join(folder, new_name)
    file_storage.save(path)
    # relatív út a static-hoz képest
    rel_path = os.path.relpath(path, os.path.join(current_app.root_path, "static")).replace("\\", "/")
    return rel_path


def process_subject_and_background(subject_file, background_file, user_id: int, is_public: bool = True):
    cfg = current_app.config
    base_static = os.path.join(current_app.root_path, "static")

    # 1) eredeti mentése
    original_rel = save_image_file(subject_file, cfg["ORIGINAL_FOLDER"])
    original_abs = os.path.join(base_static, original_rel)

    # 2) háttér mentése (ha van)
    background_rel = None
    background_obj = None
    if background_file and background_file.filename:
        background_rel = save_image_file(background_file, cfg["BACKGROUND_FOLDER"])
        background_abs = os.path.join(base_static, background_rel)

        background_obj = Background(user_id=user_id, bg_path=background_rel)
        db.session.add(background_obj)
        db.session.flush()
    else:
        background_abs = None

    # 3) rembg – kivágás
    subject_img = Image.open(original_abs).convert("RGBA")
    cutout_img = remove(subject_img)  # PIL Image-ként tér vissza

    cutout_name = f"{uuid4().hex}.png"
    cutout_abs = os.path.join(cfg["CUTOUT_FOLDER"], cutout_name)
    cutout_rel = os.path.relpath(cutout_abs, base_static).replace("\\", "/")
    cutout_img.save(cutout_abs)

    # 4) ha van háttér: összefésülés
    if background_abs:
        bg_img = Image.open(background_abs).convert("RGBA")
        bg_img = bg_img.resize(cutout_img.size, Image.LANCZOS)
        composed_img = Image.alpha_composite(bg_img, cutout_img)

        composed_name = f"{uuid4().hex}.png"
        composed_abs = os.path.join(cfg["COMPOSED_FOLDER"], composed_name)
        composed_rel = os.path.relpath(composed_abs, base_static).replace("\\", "/")
        composed_img.save(composed_abs)
    else:
        # ha nincs háttér, akkor a cutout lesz az output
        composed_rel = cutout_rel

    # 5) DB-objektumok
    img_obj = ImageModel(
        user_id=user_id,
        original_path=original_rel,
        cutout_path=cutout_rel,
    )
    db.session.add(img_obj)
    db.session.flush()

    comp_obj = Composition(
        image_id=img_obj.id,
        background_id=background_obj.id if background_obj else None,
        output_path=composed_rel,
        is_public=is_public,
    )
    db.session.add(comp_obj)
    db.session.commit()

    return comp_obj
