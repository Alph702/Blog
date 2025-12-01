from flask import (
    Blueprint,
    flash,
    request,
    render_template,
    redirect,
    url_for,
    session,
)
from container import auth_service
import logging

logger = logging.getLogger("auth.blueprint")


auth_bp: Blueprint = Blueprint("auth", __name__)
logging.debug("Auth blueprint initialized")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        logger.debug(f"Received login request: {request.form}")
        try:
            try:
                username = request.form["username"]
                password = request.form["password"]
                remember = request.form.get("remember_me")
            except KeyError as e:
                # TODO: Improve login page to match rest of the site
                logger.error(f"Missing form field: {e}", exc_info=True)
                return render_template("login.html", error="Missing form field")
            except Exception as e:
                logger.error(f"Unexpected error in login: {e}", exc_info=True)
                return render_template(
                    "login.html", error="An unexpected error occurred"
                )

            try:
                is_authenticated = auth_service.authenticate(username, password)
                if is_authenticated:
                    session["admin"] = True

                    # TODO: Remove this remember me implementation in favor of JWT-based authentication
                    if remember:
                        try:
                            logger.debug("Creating persistent token for remember me")
                            response = redirect(url_for("blog.home"))
                            token = auth_service.create_persistent_token("admin")
                            response.set_cookie(
                                "remember_me", token, max_age=30 * 24 * 60 * 60
                            )
                            return response
                        except Exception as e:
                            logger.error(
                                f"Error creating persistent token: {e}", exc_info=True
                            )
                            return render_template(
                                "login.html", error="Failed to create persistent login"
                            )
                    return redirect(url_for("blog.home"))
                else:
                    return render_template("login.html", error="Invalid credentials")
            except Exception as e:
                logger.error(f"Authentication error: {e}", exc_info=True)
                return render_template("login.html", error="Authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error in login: {e}", exc_info=True)
            return render_template("login.html", error="An unexpected error occurred")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    try:
        logger.debug("Logging out user")
        try:
            token = request.cookies.get("remember_me")
            if token:
                auth_service.revoke_token(token)
        except Exception as e:
            logger.error(f"Error revoking token: {e}", exc_info=True)
            flash("Error revoking token", "error")

        try:
            logger.debug("Clearing session data")

            session.pop("admin", None)
            response = redirect(url_for("blog.home"))
            response.delete_cookie("remember_me")
            return response
        except Exception as e:
            logger.error(f"Error during logout: {e}", exc_info=True)
            flash("Error during logout", "error")
            return redirect(url_for("blog.home"))
    except Exception as e:
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)
        flash("An unexpected error occurred during logout", "error")
        return redirect(url_for("blog.home"))
