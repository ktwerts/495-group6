"""SQLite connection handling and CLI commands (flask init-db, flask seed)."""

import sqlite3

import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """Drop and recreate all tables."""
    init_db()
    click.echo("Initialized the database.")


@click.command("seed")
@with_appcontext
def seed_command() -> None:
    """Reset the database and load sample data for local development."""
    from app.seed import seed_all

    init_db()
    password = seed_all()
    click.echo("Seeded demo data. Login: 'manager'")
    if password:
        click.echo(f"Generated password: {password}")
        click.echo("(Set SHIFTWISE_ADMIN_PASSWORD to choose your own.)")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
