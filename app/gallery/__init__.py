from flask import Blueprint

gallery_bp = Blueprint("gallery", __name__)

from . import routes
