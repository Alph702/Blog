from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from container import post_service, video_service
import logging

logger = logging.getLogger("admin.blueprint")


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
    try:
        if request.method == "POST":
            try:
                title = request.form["title"]
                content = request.form["content"]
            except KeyError as e:
                logger.error(f"Missing form field: {e}", exc_info=True)
                flash("Please fill in all required fields.", "error")
                return render_template("new.html")

            try:
                image_url = None
                if "image" in request.files:
                    image_url = post_service.upload_image(request.files["image"])
            except Exception as e:
                logger.error(f"Image upload failed: {e}", exc_info=True)
                flash("Image upload failed. Please try again.", "error")
                return render_template("new.html")

            try:
                video_id = None
                if "video" in request.files:
                    video_id = video_service.upload_video(request.files["video"])
            except Exception as e:
                logger.error(f"Video upload failed: {e}", exc_info=True)
                flash("Video upload failed. Please try again.", "error")
                return render_template("new.html")

            try:
                post_service.create_post(title, content, image_url, video_id)
                flash("Post created successfully!", "success")
                return redirect(url_for("blog.home"))
            except Exception as e:
                logger.error(f"Post creation failed: {e}", exc_info=True)
                flash("Failed to create post. Please try again, now or later.", "error")
                return render_template("new.html")

        return render_template("new.html")
    except Exception as e:
        logger.error(f"Unexpected error in new_post: {e}", exc_info=True)
        flash("An unexpected error occurred. Please try again later.", "error")
        return render_template("new.html")


@admin_bp.route("/edit/<int:post_id>", methods=["GET", "PUT"])
@admin_required
def edit_post(post_id: int):
    try:
        if request.method == "PUT":
            try:
                title = request.form.get("title")
                content = request.form.get("content")
                if not content:
                    logger.error("Content cannot be empty.", exc_info=True)
                    flash("Content cannot be empty.", "error")
                    return redirect(url_for("admin.edit_post", post_id=post_id))
                image = request.files.get("image")
                video = request.files.get("video")
            except Exception as e:
                logger.error(f"Error processing form data: {e}", exc_info=True)
                flash(
                    "There was an error with your submission. Please try again.",
                    "error",
                )
                return redirect(url_for("admin.edit_post", post_id=post_id))
            try:
                post_service.update_post(post_id, title, content, image, video)
                logger.info(f"Post {post_id} updated successfully.")
                flash("Post updated!", "success")
                return redirect(url_for("blog.home"))
            except Exception as e:
                logger.error(f"Failed to update post {post_id}: {e}", exc_info=True)
                flash("Failed to update post. Please try again later.", "error")
                return redirect(url_for("admin.edit_post", post_id=post_id))

        post = post_service.get_post_by_id(post_id)
        return render_template("edit.html", post=post)
    except Exception as e:
        logger.error(f"Unexpected error in edit_post: {e}", exc_info=True)
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for("blog.home"))


@admin_bp.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id: int):
    try:
        post_service.delete_post(post_id)
        flash("Post deleted!", "success")
        return redirect(url_for("blog.home"))
    except Exception as e:
        logger.error(f"Failed to delete post {post_id}: {e}", exc_info=True)
        flash("Failed to delete post. Please try again later.", "error")
        return redirect(url_for("blog.home"))
