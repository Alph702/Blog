from flask import Blueprint, request, jsonify, session
from container import post_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/posts")
def get_posts():
    page = request.args.get("page", 1, type=int)
    posts = post_service.get_recent_posts(page)
    has_next = post_service.has_next_page(page)

    return jsonify({"posts": posts, "has_next": has_next})


@api_bp.route("/check_admin")
def check_admin():
    return jsonify({"is_admin": session.get("admin", False)})
