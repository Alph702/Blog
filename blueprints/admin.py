from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from container import post_service, video_service
import logging

logger = logging.getLogger("admin.blueprint")


admin_bp = Blueprint("admin", __name__)


# Admin authentication decorator
def admin_required(f):
    logger.debug(f"admin_required decorator applied to {f.__name__}")

    def wrapper(*args, **kwargs):
        logger.debug(f"Checking admin requirement for {f.__name__}")
        if not session.get("admin"):
            logger.debug(f"Admin check failed, redirecting to login for {f.__name__}")
            return redirect(url_for("auth.login"))
        logger.debug(f"Admin check passed for {f.__name__}")
        return f(*args, **kwargs)

    wrapper.__name__ = f.__name__
    return wrapper


@admin_bp.route("/new", methods=["GET", "POST"])
@admin_required
def new_post():
    logger.debug("new_post() route handler called")
    try:
        # TODO: Remove unnassesary nested try-except blocks and validation
        if request.method == "POST":
            logger.debug("Processing POST request for new post")
            try:
                logger.debug("Extracting form fields: title, content")
                title = request.form["title"]
                logger.debug(f"Title extracted: {title}")
                content = request.form["content"]
                logger.debug(f"Content extracted: {content}")
            except KeyError as e:
                logger.error(f"Missing form field: {e}", exc_info=True)
                flash("Please fill in all required fields.", "error")
                return render_template("new.html")

            try:
                logger.debug("Checking for image file in request")
                image_url = None
                if "image" in request.files and request.files["image"].filename != "":
                    logger.debug("Image file found, uploading")
                    image_url = post_service.upload_image(request.files["image"])
                    logger.debug(f"Image upload completed: {image_url}")
            except Exception as e:
                logger.error(f"Image upload failed: {e}", exc_info=True)
                flash("Image upload failed. Please try again.", "error")
                return render_template("new.html")

            try:
                logger.debug("Checking for video file in request")
                video_id = None
                if "video" in request.files and request.files["video"].filename != "":
                    logger.debug("Video file found, uploading")
                    video_id = video_service.upload_video(request.files["video"])
                    logger.debug(f"Video upload completed: {video_id}")
            except Exception as e:
                logger.error(f"Video upload failed: {e}", exc_info=True)
                flash("Video upload failed. Please try again.", "error")
                return render_template("new.html")

            try:
                logger.debug(f"Calling post_service.create_post with title: {title}")
                post_service.create_post(title, content, image_url, video_id)
                logger.debug("Post created successfully")
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


@admin_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@admin_required
def edit_post(post_id: int):
    logger.debug(f"edit_post() route handler called with post_id: {post_id}")
    try:
        if request.method == "POST":
            logger.debug(f"Processing POST request for post_id: {post_id}")
            try:
                logger.debug("Extracting form fields: title, content, image, video")
                title = request.form.get("title")
                logger.debug(f"Title: {title}")
                content = request.form.get("content")
                logger.debug("Content extracted")
                if not content:
                    logger.error("Content cannot be empty.", exc_info=True)
                    flash("Content cannot be empty.", "error")
                    return redirect(url_for("admin.edit_post", post_id=post_id))
                image = request.files.get("image")
                logger.debug(f"Image file: {bool(image)}")
                video = request.files.get("video")
                logger.debug(f"Video file: {bool(video)}")
            except Exception as e:
                logger.error(f"Error processing form data: {e}", exc_info=True)
                flash(
                    "There was an error with your submission. Please try again.",
                    "error",
                )
                return redirect(url_for("admin.edit_post", post_id=post_id))
            try:
                logger.debug(f"Calling post_service.update_post for post_id: {post_id}")
                post_service.update_post(post_id, title, content, image, video)
                logger.debug(f"Post {post_id} updated successfully.")
                flash("Post updated!", "success")
                return redirect(url_for("blog.home"))
            except Exception as e:
                logger.error(f"Failed to update post {post_id}: {e}", exc_info=True)
                flash("Failed to update post. Please try again later.", "error")
                return redirect(url_for("admin.edit_post", post_id=post_id))

        post = post_service.get_post_by_id(post_id)
        logger.debug(f"Rendering edit.html for post_id: {post_id}")
        return render_template("edit.html", post=post)
    except Exception as e:
        logger.error(f"Unexpected error in edit_post: {e}", exc_info=True)
        flash("An unexpected error occurred. Please try again later.", "error")
        return redirect(url_for("blog.home"))


@admin_bp.route("/delete/<int:post_id>")
@admin_required
def delete_post(post_id: int):
    logger.debug(f"delete_post() route handler called with post_id: {post_id}")
    try:
        logger.debug(f"Calling post_service.delete_post({post_id})")
        post_service.delete_post(post_id)
        logger.debug(f"Post {post_id} deleted successfully")
        flash("Post deleted!", "success")
        return redirect(url_for("blog.home"))
    except Exception as e:
        logger.error(f"Failed to delete post {post_id}: {e}", exc_info=True)
        flash("Failed to delete post. Please try again later.", "error")
        return redirect(url_for("blog.home"))
