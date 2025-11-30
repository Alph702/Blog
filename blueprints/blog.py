from typing import Any, Dict
from flask import Blueprint, render_template, request, session, send_from_directory
from container import post_service

blog_bp: Blueprint = Blueprint("blog", __name__)


@blog_bp.route("/")
def home():
    posts = post_service.get_recent_posts()
    return render_template("index.html", posts=posts, admin=session.get("admin", False))


@blog_bp.route("/filter")
def filter_posts():
    year: str = request.args.get("year", "any")
    month: str = request.args.get("month", "any")
    day: str = request.args.get("day", "any")

    # TODO: create a system to get posts by date pur page
    posts: list[Dict[str, Any]] = post_service.filter_posts(year, month, day)
    return render_template("index.html", posts=posts)


@blog_bp.route("/post/<int:post_id>")
def view_post(post_id: int):
    post = post_service.get_post_by_id(post_id)
    return render_template("post.html", post=post)

@blog_bp.route("/<path:path>")
def serve_static(path: str):
    return send_from_directory(directory="static", path=path)