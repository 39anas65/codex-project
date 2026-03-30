"""Flask application for the document verification blockchain service."""

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from .core import Blockchain


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    blockchain = Blockchain()
    app.config["blockchain"] = blockchain

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
        if not request.content_type or "multipart/form-data" not in request.content_type:
            return jsonify({"error": "Request body must be multipart/form-data."}), 400

        upload = request.files.get("document_file")
        if upload is None:
            return jsonify({"error": "document_file is required"}), 400

        filename = secure_filename(upload.filename or "").strip()
        if not filename:
            return jsonify({"error": "document_file must include a filename"}), 400

        file_bytes = upload.read()
        if not file_bytes:
            return jsonify({"error": "document_file cannot be empty"}), 400

        payload = request.form.to_dict(flat=True)
        if not str(payload.get("document_name", "")).strip():
            payload["document_name"] = filename

        payload["document_hash"] = blockchain.build_document_hash(file_bytes, payload)
        document = blockchain.add_document(payload)
        response = {
            "message": "Document record added to pending queue.",
            "pending_count": len(blockchain.pending_documents),
            "document_hash": document["document_hash"],
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
