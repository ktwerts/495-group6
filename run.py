"""Development entry point: `python run.py` (or `flask --app run run`)."""

from dotenv import load_dotenv

load_dotenv()  # read .env before config is imported

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
