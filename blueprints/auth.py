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
    logger.debug("login() route handler called")
    if request.method == "POST":
        logger.debug(f"Received login request: {request.form}")
        try:
            try:
                logger.debug("Extracting form fields: username, password, remember_me")
                username = request.form["username"]
                logger.debug(f"Username extracted: {username}")
                password = request.form["password"]
                logger.debug("Password extracted")
                remember = request.form.get("remember_me")
                logger.debug(f"Remember me: {remember}")
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
                logger.debug(f"Calling auth_service.authenticate for user: {username}")
                is_authenticated = auth_service.authenticate(username, password)
                logger.debug(f"Authentication result: {is_authenticated}")
                if is_authenticated:
                    logger.debug("Setting session admin flag to True")
                    session["admin"] = True

                    # TODO: Remove this remember me implementation in favor of JWT-based authentication
                    if remember:
                        logger.debug(
                            "Remember me is enabled, creating persistent token"
                        )
                        try:
                            logger.debug("Creating persistent token for remember me")
                            response = redirect(url_for("blog.home"))
                            logger.debug("Calling auth_service.create_persistent_token")
                            token = auth_service.create_persistent_token("admin")
                            logger.debug("Token created, setting cookie")
                            response.set_cookie(
                                "remember_me", token, max_age=30 * 24 * 60 * 60
                            )
                            logger.debug("Redirecting to home with remember me cookie")
                            return response
                        except Exception as e:
                            logger.error(
                                f"Error creating persistent token: {e}", exc_info=True
                            )
                            return render_template(
                                "login.html", error="Failed to create persistent login"
                            )
                    logger.debug("Redirecting to home without remember me")
                    return redirect(url_for("blog.home"))
                else:
                    logger.warning("Authentication failed: invalid credentials")
                    return render_template("login.html", error="Invalid credentials")
            except Exception as e:
                logger.error(f"Authentication error: {e}", exc_info=True)
                return render_template("login.html", error="Authentication failed")
        except Exception as e:
            logger.error(f"Unexpected error in login: {e}", exc_info=True)
            return render_template("login.html", error="An unexpected error occurred")
    logger.debug("GET request to login, rendering login template")
    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    logger.debug("logout() route handler called")
    try:
        logger.debug("Logging out user")
        try:
            logger.debug("Checking for remember_me cookie")
            token = request.cookies.get("remember_me")
            logger.debug(f"Token found: {bool(token)}")
            if token:
                logger.debug("Revoking persistent token")
                auth_service.revoke_token(token)
        except Exception as e:
            logger.error(f"Error revoking token: {e}", exc_info=True)
            flash("Error revoking token", "error")

        try:
            logger.debug("Clearing session data")
            logger.debug("Popping admin from session")
            session.pop("admin", None)
            logger.debug("Creating redirect response to home")
            response = redirect(url_for("blog.home"))
            logger.debug("Deleting remember_me cookie")
            response.delete_cookie("remember_me")
            logger.debug("Logout successful, returning redirect")
            return response
        except Exception as e:
            logger.error(f"Error during logout: {e}", exc_info=True)
            flash("Error during logout", "error")
            return redirect(url_for("blog.home"))
    except Exception as e:
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)
        flash("An unexpected error occurred during logout", "error")
        return redirect(url_for("blog.home"))
