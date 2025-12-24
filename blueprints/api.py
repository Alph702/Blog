from flask import Blueprint, request, jsonify, session
from container import post_service
import logging

logger = logging.getLogger("api.blueprint")

api_bp = Blueprint("api", __name__, url_prefix="/api")
logging.debug("API blueprint initialized")


@api_bp.route("/posts")
def get_posts():
    logger.debug("get_posts() API route handler called")
    try:
        logger.debug("Extracting page parameter from request")
        page = request.args.get("page", 1, type=int)
        logger.debug(f"Page number: {page}")
        try:
            logger.debug(f"Calling post_service.get_recent_posts({page})")
            posts = post_service.get_recent_posts(page)
            logger.debug(f"Retrieved {len(posts.posts)} posts for page {page}")
        except Exception as e:
            logger.error(f"Error fetching posts for page {page}: {e}", exc_info=True)
            return jsonify({"error": "Failed to fetch posts"}), 500

        return jsonify({"posts": [post.model_dump(mode="json") for post in posts.posts], "has_next": posts.has_next_page})
    except Exception as e:
        logger.error(f"Unexpected error in get_posts: {e}", exc_info=True)
        logger.debug("Returning error response")
        return jsonify({"error": "An unexpected error occurred"}), 500


@api_bp.route("/check_admin")
def check_admin():
    logger.debug("check_admin() API route handler called")
    logger.debug("Checking admin status")
    is_admin = session.get("admin", False)
    logger.debug(f"Admin status: {is_admin}")
    return jsonify({"is_admin": is_admin})


@api_bp.route("/upload-video", methods=["POST"])
def upload_video():
    """Upload a video file and return the video ID for later form submission."""
    logger.debug("upload_video() API route handler called")
    
    # Check if user is admin
    if not session.get("admin"):
        logger.warning("Unauthorized video upload attempt")
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        if "video" not in request.files:
            logger.error("No video file in request")
            return jsonify({"error": "No video file provided"}), 400
        
        video_file = request.files["video"]
        if video_file.filename == "":
            logger.error("Empty video filename")
            return jsonify({"error": "No video file selected"}), 400
        
        from container import video_service
        
        logger.debug(f"Uploading video: {video_file.filename}")
        video_id = video_service.upload_video(video_file)
        
        if video_id:
            logger.debug(f"Video uploaded successfully with ID: {video_id}")
            return jsonify({"success": True, "video_id": video_id})
        else:
            logger.error("Video upload returned no ID")
            return jsonify({"error": "Video upload failed"}), 500
            
    except Exception as e:
        logger.error(f"Video upload error: {e}", exc_info=True)
        return jsonify({"error": "Video upload failed"}), 500
