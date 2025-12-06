from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    session,
    send_from_directory,
    redirect,
    url_for,
)
from container import post_service
import logging

logger = logging.getLogger("blog.blueprint")


blog_bp: Blueprint = Blueprint("blog", __name__)

logging.debug("Blog blueprint initialized")


@blog_bp.route("/")
def home():
    logger.debug("home() route handler called")
    try:
        logger.debug("Calling post_service.get_recent_posts()")
        posts = post_service.get_recent_posts()
        logger.debug(f"Retrieved {len(posts.posts)} posts")
        logger.debug(f"Rendering index.html with {len(posts.posts)} posts")
        return render_template(
            "index.html", posts=posts.posts, admin=session.get("admin", False)
        )
    except Exception as e:
        logger.critical(f"Error fetching recent posts: {e}")
        posts = []
        flash("Failed to load posts", "error")
        return render_template(
            "index.html", posts=posts, admin=session.get("admin", False)
        )


@blog_bp.route("/filter")
def filter_posts():
    logger.debug("filter_posts() route handler called")
    year: str = request.args.get("year", "any")
    month: str = request.args.get("month", "any")
    day: str = request.args.get("day", "any")
    logger.debug(f"Filter params - year: {year}, month: {month}, day: {day}")

    # TODO: create a system to get posts by date pur page
    try:
        logger.debug("Calling post_service.filter_posts()")
        posts = post_service.filter_posts(year, month, day)
        logger.debug(f"Filtered posts retrieved: {len(posts.posts)}")
        logger.debug("Rendering index.html with filtered posts")
        return render_template(
            "index.html", posts=posts.posts, admin=session.get("admin", False)
        )
    except Exception as e:
        logger.error(
            f"Error filtering posts by date {year}-{month}-{day}: {e}", exc_info=True
        )
        posts = []
        flash("Failed to filter posts", "error")
        return render_template(
            "index.html", posts=posts, admin=session.get("admin", False)
        )


@blog_bp.route("/post/<int:post_id>")
def view_post(post_id: int):
    logger.debug(f"view_post() route handler called with post_id: {post_id}")
    try:
        logger.debug(f"Calling post_service.get_post_by_id({post_id})")
        post = post_service.get_post_by_id(post_id)
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {e}", exc_info=True)
        post = None
        flash("Failed to load post", "error")
        return redirect(url_for("blog.home"))
    logger.debug(f"Rendering post.html for post_id: {post_id}")
    return render_template("post.html", post=post)


@blog_bp.route("/static/<path:path>")
def serve_static(path: str):
    logger.debug(f"serve_static() route handler called for path: {path}")
    try:
        logger.debug(f"Serving static file {path}")
        return send_from_directory(directory="static", path=path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}", exc_info=True)
        logger.debug(f"Returning 404 for static file {path}")
        return "File not found", 404
