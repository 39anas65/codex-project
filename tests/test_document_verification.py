"""Tests for upload-based document registration and verification."""

from io import BytesIO
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from document_verification import Blockchain, create_app


@pytest.fixture()
def client():
    """Return a Flask test client for the API."""
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def add_document(client, content, filename="record.txt", **metadata):
    """Submit a multipart document registration request."""
    data = {
        "document_file": (BytesIO(content), filename),
        **metadata,
    }
    return client.post("/add_document", data=data, content_type="multipart/form-data")


def test_add_document_upload_returns_hash_and_pending_record(client):
    response = add_document(
        client,
        b"hello blockchain",
        document_name="hello.txt",
        issuer="OpenAI Academy",
        document_summary="Greeting example document",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["pending_count"] == 1
    assert payload["document_hash"]
    assert payload["document"]["document_hash"] == payload["document_hash"]
    assert payload["document"]["document_summary"] == "Greeting example document"
    assert payload["document"]["submitted_at"]


def test_add_document_requires_uploaded_file(client):
    response = client.post(
        "/add_document",
        data={"document_name": "missing.txt"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "document_file is required"


def test_same_file_and_metadata_produce_same_hash():
    blockchain = Blockchain()
    payload = {
        "document_name": "report.pdf",
        "issuer": "Example Org",
        "owner": "Jane Doe",
        "document_type": "certificate",
        "issued_at": "2026-03-30",
        "document_summary": "Quarterly compliance certificate",
    }

    first_hash = blockchain.build_document_hash(b"file-contents", payload)
    second_hash = blockchain.build_document_hash(b"file-contents", dict(payload))

    assert first_hash == second_hash


def test_same_file_and_different_metadata_produce_different_hashes():
    blockchain = Blockchain()
    first_hash = blockchain.build_document_hash(
        b"file-contents",
        {"document_name": "report.pdf", "document_summary": "Version one"},
    )
    second_hash = blockchain.build_document_hash(
        b"file-contents",
        {"document_name": "report.pdf", "document_summary": "Version two"},
    )

    assert first_hash != second_hash


def test_add_document_defaults_document_name_from_filename(client):
    response = add_document(client, b"file-bytes", filename="fallback-name.pdf")

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["document"]["document_name"] == "fallback-name.pdf"


def test_mined_block_contains_uploaded_document_summary_and_verifies(client):
    add_response = add_document(
        client,
        b"verified payload",
        filename="proof.pdf",
        document_summary="Proof document",
    )
    document_hash = add_response.get_json()["document_hash"]

    mine_response = client.get("/mine_block")
    assert mine_response.status_code == 200
    mine_payload = mine_response.get_json()
    assert mine_payload["documents"][0]["document_summary"] == "Proof document"

    verify_response = client.get(f"/verify_document/{document_hash}")
    assert verify_response.status_code == 200
    verify_payload = verify_response.get_json()
    assert verify_payload["verified"] is True
    assert verify_payload["document"]["document_hash"] == document_hash
