"""Flask application for the document verification blockchain service."""

import os
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename

from .core import Blockchain
from .storage import BlockchainRepository

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "blockchain.db"


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = os.getenv(
        "BLOCKCHAIN_DB_PATH", str(DEFAULT_DATABASE_PATH)
    )
    if config:
        app.config.update(config)

    repository = BlockchainRepository(app.config["DATABASE_PATH"])
    blockchain = Blockchain(repository=repository)
    app.config["blockchain"] = blockchain
    app.config["repository"] = repository

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.route("/mine_block", methods=["GET"])
    def mine_block():
        """Mine a new block and return its contents."""
        block = blockchain.mine_pending_documents()
        response = {
            "message": "Congratulations, you just mined a block!",
            "index": block["index"],
            "timestamp": block["timestamp"],
            "proof": block["proof"],
            "previous_hash": block["previous_hash"],
            "documents": block["documents"],
        }
        return jsonify(response), 200

    @app.route("/get_chain", methods=["GET"])
    def get_chain():
        """Return the full blockchain and its current length."""
        response = {"chain": blockchain.chain, "length": len(blockchain.chain)}
        return jsonify(response), 200

    @app.route("/is_valid", methods=["GET"])
    def is_valid():
        """Return whether the current blockchain passes validation checks."""
        chain_is_valid = blockchain.is_chain_valid(blockchain.chain)
        if chain_is_valid:
            response = {
                "message": "All good. The Blockchain is valid.",
                "is_valid": True,
            }
        else:
            response = {
                "message": "Houston, we have a problem. The Blockchain is not valid.",
                "is_valid": False,
            }
        return jsonify(response), 200

    @app.route("/add_document", methods=["POST"])
    def add_document():
        """Queue a document record to be included in the next mined block."""
        is_multipart = bool(request.content_type) and (
            "multipart/form-data" in request.content_type
        )
        if is_multipart:
            uploaded_file = request.files.get("document_file") or request.files.get("file")
            if uploaded_file is None:
                return jsonify({"error": "document_file is required"}), 400

            filename = secure_filename(uploaded_file.filename or "").strip()
            if not filename:
                return jsonify({"error": "document_file must include a filename"}), 400

            file_bytes = uploaded_file.read()
            if not file_bytes:
                return jsonify({"error": "document_file cannot be empty"}), 400

            payload = {
                "document_name": _clean_text(request.form.get("document_name")) or filename,
                "issuer": _clean_text(request.form.get("issuer")),
                "owner": _clean_text(request.form.get("owner")),
                "document_type": _clean_text(request.form.get("document_type")),
                "issued_at": _clean_text(request.form.get("issued_at")),
                "document_summary": _clean_text(request.form.get("document_summary")),
                "file_name": filename,
                "content_type": uploaded_file.mimetype or "application/octet-stream",
                "file_size": len(file_bytes),
            }
            payload["document_hash"] = blockchain.build_document_hash(file_bytes, payload)
            document = blockchain.add_document(payload, file_bytes=file_bytes)
            response = {
                "message": "Document record added to pending queue.",
                "pending_count": len(blockchain.pending_documents),
                "document_hash": document["document_hash"],
                "document_id": document.get("id"),
                "document": document,
            }
            return jsonify(response), 201

        try:
            payload = request.get_json(force=False, silent=False)
        except BadRequest:
            return jsonify({"error": "Request body must be valid JSON."}), 400

        if payload is None or not isinstance(payload, dict):
            return jsonify({"error": "Request body must be valid JSON."}), 400

        document_hash = str(payload.get("document_hash", "")).strip()
        if not document_hash:
            return jsonify({"error": "document_hash is required"}), 400

        document = blockchain.add_document(payload)
        response = {
            "message": "Document record added to pending queue.",
            "pending_count": len(blockchain.pending_documents),
            "document_hash": document["document_hash"],
            "document_id": document.get("id"),
            "document": document,
        }
        return jsonify(response), 201

    @app.route("/pending_documents", methods=["GET"])
    def pending_documents():
        """Return the current pending document queue."""
        documents = blockchain.get_pending_documents()
        response = {"pending_documents": documents, "pending_count": len(documents)}
        return jsonify(response), 200

    @app.route("/verify_document/<document_hash>", methods=["GET"])
    def verify_document(document_hash):
        """Check whether a document hash exists in any mined block."""
        verification = blockchain.verify_document(document_hash)
        return jsonify(verification), 200

    return app


def _clean_text(value):
    """Normalize optional text form values."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None
