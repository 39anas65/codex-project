"""Run the Flask backend for the document verification blockchain service."""

from document_verification import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
