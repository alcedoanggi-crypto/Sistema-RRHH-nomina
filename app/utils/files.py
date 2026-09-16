import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def save_upload(file_storage, subcarpeta=""):
    """Guarda un archivo y devuelve la ruta relativa a static/ (para url_for('static', ...))."""
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Tipo de archivo no permitido")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    nombre = f"{uuid.uuid4().hex}.{ext}"
    destino_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subcarpeta)
    os.makedirs(destino_dir, exist_ok=True)
    file_storage.save(os.path.join(destino_dir, nombre))

    rel = os.path.join(
        os.path.basename(current_app.config["UPLOAD_FOLDER"]), subcarpeta, nombre
    )
    return rel.replace("\\", "/")
