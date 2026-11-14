"""Sample data for local development and demos (run with `flask seed`)."""

import os
import secrets

from app.auth.service import create_user


def seed_all() -> str | None:
    """Create demo data. Returns the generated password, or None if it came from the env.

    TODO (each owner adds sample data for their module):
      - Interface Designer: sample employees with qualifications and availability,
        plus an employee-role login linked to one of them
      - Lead Architect: a week of shifts (leave a few open to demo replacements)
      - Integration Lead: several months of staffing history for training the model
        (synthetic is fine for alpha; note it in docs/technical-debt.md)
    """
    password = os.environ.get("SHIFTWISE_ADMIN_PASSWORD")
    generated = None
    if not password:
        password = generated = secrets.token_urlsafe(12)
    create_user("manager", password, "manager")
    return generated
