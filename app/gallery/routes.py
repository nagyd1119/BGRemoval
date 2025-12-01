from datetime import datetime
from flask import (
    render_template, request, redirect, url_for,
    flash, g
)
from . import gallery_bp
from .utils import allowed_file, process_subject_and_background
from ..models import Composition, Comment, Image
from .. import db
from ..auth.routes import login_required, can_edit_resource


@gallery_bp.route("/", methods=["GET", "POST"])
def gallery():
    if request.method == "POST":
        if g.user is None:
            flash("You need to be logged in to upload images.")
            return redirect(url_for("auth.login"))

        subject_file = request.files.get("subject")
        background_file = request.files.get("background")

        if not subject_file or subject_file.filename == "":
            flash("Frontal image not found.")
            return redirect(url_for("gallery.gallery"))

        if not allowed_file(subject_file.filename):
            flash("Frontal image type not supported.")
            return redirect(url_for("gallery.gallery"))

        if background_file and background_file.filename and not allowed_file(background_file.filename):
            flash("Background image type not supported.")
            return redirect(url_for("gallery.gallery"))

        visibility = request.form.get("visibility", "public")
        is_public = (visibility == "public")

        comp = process_subject_and_background(
            subject_file,
            background_file,
            g.user.id,
            is_public=is_public,
        )
        flash("Finished")
        return redirect(url_for("gallery.composition_detail", comp_id=comp.id))

    query = Composition.query

    if g.user is None:
        query = query.filter(Composition.is_public.is_(True))
    elif g.user.is_admin:
        pass
    else:
        query = (
            query.outerjoin(Image)
            .filter(
                db.or_(
                    Composition.is_public.is_(True),
                    Image.user_id == g.user.id,
                )
            )
        )

    compositions = query.order_by(Composition.created_at.desc()).all()
    return render_template("gallery/gallery.html", compositions=compositions)


@gallery_bp.route("/composition/<int:comp_id>", methods=["GET", "POST"])
def composition_detail(comp_id):
    comp = Composition.query.get_or_404(comp_id)

    owner_id = comp.image.user_id if comp.image else None
    if not comp.is_public:
        if g.user is None or (not g.user.is_admin and g.user.id != owner_id):
            flash("This image is private.")
            return redirect(url_for("gallery.gallery"))

    if request.method == "POST":
        if g.user is None:
            flash("You need to be logged in to post comments.")
            return redirect(url_for("auth.login"))

        text = request.form.get("text", "").strip()
        if not text:
            flash("Comment cannot be empty.")
        else:
            comment = Comment(
                user_id=g.user.id,
                composition_id=comp.id,
                text=text
            )
            db.session.add(comment)
            db.session.commit()
            flash("Comment successfully posted.")

        return redirect(url_for("gallery.composition_detail", comp_id=comp.id))

    return render_template("gallery/composition_detail.html", composition=comp)


@gallery_bp.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if not can_edit_resource(comment.user_id, g.user):
        flash("You have no permission to edit this comment.")
        return redirect(url_for("gallery.composition_detail", comp_id=comment.composition_id))

    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Comment cannot be empty.")
        else:
            comment.text = text
            comment.is_edited = True
            comment.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Comment updated.")
            return redirect(url_for("gallery.composition_detail", comp_id=comment.composition_id))

    return render_template("gallery/edit_comment.html", comment=comment)


@gallery_bp.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if not can_edit_resource(comment.user_id, g.user):
        flash("You have no permission to delete this comment.")
        return redirect(url_for("gallery.composition_detail", comp_id=comment.composition_id))

    comp_id = comment.composition_id
    db.session.delete(comment)
    db.session.commit()
    flash("Comment successfully deleted.")
    return redirect(url_for("gallery.composition_detail", comp_id=comp_id))


@gallery_bp.route("/composition/<int:comp_id>/set_profile", methods=["POST"])
@login_required
def set_profile_image(comp_id):
    comp = Composition.query.get_or_404(comp_id)

    owner_id = comp.image.user_id if comp.image else None

    if not comp.is_public:
        if not g.user.is_admin and g.user.id != owner_id:
            flash("This image is private, you may not set it as profile picture")
            return redirect(url_for("gallery.composition_detail", comp_id=comp.id))

    g.user.profile_image_id = comp.id
    db.session.commit()
    flash("Profile picture successfully updated.")
    return redirect(url_for("gallery.composition_detail", comp_id=comp.id))

