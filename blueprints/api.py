from flask import Blueprint, request, jsonify, session
from container import post_service
import logging

logger = logging.getLogger("api.blueprint")

api_bp = Blueprint("api", __name__, url_prefix="/api")
logging.debug("API blueprint initialized")


@api_bp.route("/posts")
def get_posts():
    try:
        page = request.args.get("page", 1, type=int)
        try:
            posts = post_service.get_recent_posts(page)
        except Exception as e:
            logger.error(f"Error fetching posts for page {page}: {e}", exc_info=True)
            return jsonify({"error": "Failed to fetch posts"}), 500
        try:
            has_next = post_service.has_next_page(page)
        except Exception as e:
            logger.error(
                f"Error checking next page for page {page}: {e}", exc_info=True
            )
            return jsonify({"error": "Failed to check next page"}), 500

        return jsonify({"posts": posts, "has_next": has_next})
    except Exception as e:
        logger.error(f"Unexpected error in get_posts: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500


@api_bp.route("/check_admin")
def check_admin():
    logger.debug("Checking admin status")
    return jsonify({"is_admin": session.get("admin", False)})
