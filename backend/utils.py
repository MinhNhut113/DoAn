"""Utility helpers for backend routes."""
from flask_jwt_extended import get_jwt_identity


def get_current_user_id():
    """Return the current JWT identity as int if possible, otherwise raw identity.

    This normalizes cases where the JWT identity may be stored as a string or int.
    """
    ident = get_jwt_identity()
    try:
        return int(ident)
    except Exception:
        return ident


def parse_possible_int(val):
    try:
        return int(val)
    except Exception:
        return val
