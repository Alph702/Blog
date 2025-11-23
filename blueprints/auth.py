from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    redirect,
    url_for,
    session,
)
from container import auth_service

auth_bp: Blueprint = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form.get("remember")

        if auth_service.authenticate(username, password):
            session["admin"] = True

            # TODO: Remove this remember me implementation in favor of JWT-based authentication
            if remember:
                response = redirect(url_for("blog.home"))
                token = auth_service.create_persistent_token("admin")
                response.set_cookie("remember_me", token, max_age=30 * 24 * 60 * 60)
                return response

            return redirect(url_for("blog.home"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    token = request.cookies.get("remember_me")
    if token:
        auth_service.revoke_token(token)

    session.pop("admin", None)
    response = redirect(url_for("blog.home"))
    response.delete_cookie("remember_me")
    return response


@auth_bp.route("/check_session")
def check_session():
    return jsonify({"admin": session.get("admin", False)})
