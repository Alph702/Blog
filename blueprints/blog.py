from typing import Any, Dict
from flask import Blueprint, flash, render_template, request, session, send_from_directory, redirect, url_for
from container import post_service
import logging

logger = logging.getLogger("blog.blueprint")


blog_bp: Blueprint = Blueprint("blog", __name__)

logging.debug("Blog blueprint initialized")

@blog_bp.route("/")
def home():
    try:
        posts = post_service.get_recent_posts()
    except Exception as e:
        logger.critical(f"Error fetching recent posts: {e}")
        posts = []
        flash("Failed to load posts", "error")
    return render_template("index.html", posts=posts, admin=session.get("admin", False))


@blog_bp.route("/filter")
def filter_posts():
    year: str = request.args.get("year", "any")
    month: str = request.args.get("month", "any")
    day: str = request.args.get("day", "any")

    # TODO: create a system to get posts by date pur page
    try:
        posts: list[Dict[str, Any]] = post_service.filter_posts(year, month, day)
    except Exception as e:
        logger.error(f"Error filtering posts by date {year}-{month}-{day}: {e}")
        posts = []
        flash("Failed to filter posts", "error")
    return render_template("index.html", posts=posts)


@blog_bp.route("/post/<int:post_id>")
def view_post(post_id: int):
    logger.debug(f"Viewing post {post_id}")
    try:
        post = post_service.get_post_by_id(post_id)
    except Exception as e:
        logger.error(f"Error fetching post {post_id}: {e}")
        post = None
        flash("Failed to load post", "error")
        return redirect(url_for("blog.home"))
    return render_template("post.html", post=post)


@blog_bp.route("/<path:path>")
def serve_static(path: str):
    logger.debug(f"Serving static file {path}")
    return send_from_directory(directory="static", path=path)
