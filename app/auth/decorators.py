"""Route guards. Use @login_required or @role_required("manager") on views."""

from functools import wraps

from flask import abort, g, redirect, request, url_for


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            if request.path.startswith("/api/"):
                abort(401, description="Authentication required")
            return redirect(url_for("auth.login_page"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if g.user["role"] not in roles:
                abort(403, description="You do not have permission to do that")
            return view(*args, **kwargs)

        return wrapped

    return decorator
