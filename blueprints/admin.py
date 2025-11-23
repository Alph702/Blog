from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from container import post_service, video_service

admin_bp = Blueprint("admin", __name__)


# Admin authentication decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


@admin_bp.route("/new", methods=["GET", "POST"])
@admin_required
def new_post():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        image_url = None
        if "image" in request.files:
            image_url = post_service.upload_image(request.files["image"])

        video_id = None
        if "video" in request.files:
            video_id = video_service.upload_video(request.files["video"])

        post_service.create_post(title, content, image_url, video_id)
        flash("Post created successfully!", "success")
        return redirect(url_for("blog.home"))

    return render_template("new.html")


@admin_bp.route("/edit/<int:post_id>", methods=["GET", "PUT"])
@admin_required
def edit_post(post_id: int):
    if request.method == "PUT":
        post_service.update_post(post_id, request.form, request.files)
        flash("Post updated!", "success")
        return redirect(url_for("blog.home"))

    post = post_service.get_post_by_id(post_id)
    return render_template("edit.html", post=post)


@admin_bp.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id: int):
    post_service.delete_post(post_id)
    flash("Post deleted!", "success")
    return redirect(url_for("blog.home"))
