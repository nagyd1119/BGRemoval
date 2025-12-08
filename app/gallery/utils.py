import os
from uuid import uuid4
import uuid
from PIL import Image as PILImage
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
    rel_path = os.path.relpath(path, os.path.join(current_app.root_path, "static")).replace("\\", "/")
    return rel_path


def process_subject_and_background(subject_file, background_file, user_id: int, is_public: bool = True):
    cfg = current_app.config
    base_static = os.path.join(current_app.root_path, "static")

    original_rel = save_image_file(subject_file, cfg["ORIGINAL_FOLDER"])
    original_abs = os.path.join(base_static, original_rel)

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

    subject_img = PILImage.open(original_abs).convert("RGBA")
    cutout_img = remove(subject_img)

    cutout_name = f"{uuid4().hex}.png"
    cutout_abs = os.path.join(cfg["CUTOUT_FOLDER"], cutout_name)
    cutout_rel = os.path.relpath(cutout_abs, base_static).replace("\\", "/")
    cutout_img.save(cutout_abs)

    if background_abs:
        bg_img = PILImage.open(background_abs).convert("RGBA")
        bg_img = bg_img.resize(cutout_img.size, PILImage.LANCZOS)
        composed_img = PILImage.alpha_composite(bg_img, cutout_img)

        composed_name = f"{uuid4().hex}.png"
        composed_abs = os.path.join(cfg["COMPOSED_FOLDER"], composed_name)
        composed_rel = os.path.relpath(composed_abs, base_static).replace("\\", "/")
        composed_img.save(composed_abs)
    else:
        composed_rel = cutout_rel

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

def recompose_with_new_background(composition: Composition, background_file):
    cfg = current_app.config
    base_static = os.path.join(current_app.root_path, "static")

    bg_rel_path = save_image_file(background_file, cfg["BACKGROUND_FOLDER"])
    bg_abs = os.path.join(base_static, bg_rel_path)

    bg = Background(
        user_id=composition.image.user_id if composition.image else None,
        bg_path=bg_rel_path,
    )
    db.session.add(bg)
    db.session.flush()

    static_root = current_app.static_folder
    cutout_abs = os.path.join(static_root, composition.image.cutout_path)
    bg_abs = os.path.join(static_root, bg_rel_path)

    fg = PILImage.open(cutout_abs).convert("RGBA")
    bg_img = PILImage.open(bg_abs).convert("RGBA")

    bg_img = bg_img.resize(fg.size, PILImage.LANCZOS)

    merged = PILImage.new("RGBA", fg.size)
    merged.paste(bg_img, (0, 0))
    merged.alpha_composite(fg)

    file_name = f"{uuid.uuid4().hex}.png"
    out_rel = os.path.join("compositions", file_name).replace("\\", "/")
    out_abs = os.path.join(static_root, out_rel)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    merged.save(out_abs, "PNG")

    old_out_rel = composition.output_path
    if old_out_rel:
        old_out_abs = os.path.join(static_root, old_out_rel)
        try:
            os.remove(old_out_abs)
        except OSError:
            pass

    composition.background_id = bg.id
    composition.output_path = out_rel

    db.session.commit()
    return composition