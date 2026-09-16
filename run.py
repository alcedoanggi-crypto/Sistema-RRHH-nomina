import os
from app import create_app
from app.extensions import db
from app import models  # noqa: F401  (registra los modelos)

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "models": models}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=app.config.get("DEBUG", True))
