import hashlib
import io
import sqlite3

import pytest

from document_verification.api import create_app


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "blockchain-test.db"


@pytest.fixture
def app(database_path):
    app = create_app({"TESTING": True, "DATABASE_PATH": str(database_path)})
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_app_creates_single_genesis_block_and_reloads_it(database_path):
    first_app = create_app({"TESTING": True, "DATABASE_PATH": str(database_path)})
    second_app = create_app({"TESTING": True, "DATABASE_PATH": str(database_path)})

    assert len(first_app.config["blockchain"].chain) == 1
    assert len(second_app.config["blockchain"].chain) == 1
    assert first_app.config["blockchain"].chain[0]["index"] == 1
    assert second_app.config["blockchain"].chain[0]["index"] == 1


def test_upload_persists_binary_file_and_metadata(client, database_path):
    payload = b"%PDF-1.4 fake pdf bytes"
    response = client.post(
        "/add_document",
        data={
            "file": (io.BytesIO(payload), "certificate.pdf"),
            "document_name": "Course Certificate",
            "issuer": "ABC Academy",
            "owner": "John Doe",
            "document_type": "certificate",
            "issued_at": "2026-03-30",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["pending_count"] == 1
    assert data["document"]["file_name"] == "certificate.pdf"
    assert data["document"]["file_size"] == len(payload)
    assert data["document_hash"] == hashlib.sha256(payload).hexdigest()

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT file_name, content_type, file_size, file_data, status FROM documents"
        ).fetchone()

    assert row[0] == "certificate.pdf"
    assert row[1] == "application/pdf"
    assert row[2] == len(payload)
    assert row[3] == payload
    assert row[4] == "pending"


def test_upload_accepts_text_files_and_mining_persists_chain_state(client, database_path):
    payload = b"hello from a text file"
    upload_response = client.post(
        "/add_document",
        data={
            "file": (io.BytesIO(payload), "notes.txt"),
            "owner": "Alice",
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 201

    mine_response = client.get("/mine_block")
    assert mine_response.status_code == 200
    mined_block = mine_response.get_json()
    assert mined_block["index"] == 2
    assert len(mined_block["documents"]) == 1
    assert mined_block["documents"][0]["file_name"] == "notes.txt"

    with sqlite3.connect(database_path) as connection:
        block_count = connection.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        status = connection.execute("SELECT status FROM documents").fetchone()[0]

    assert block_count == 2
    assert status == "mined"

    restarted_app = create_app({"TESTING": True, "DATABASE_PATH": str(database_path)})
    restarted_chain = restarted_app.config["blockchain"].chain
    assert len(restarted_chain) == 2
    assert restarted_chain[1]["documents"][0]["document_hash"] == hashlib.sha256(payload).hexdigest()


def test_verify_document_returns_persisted_mined_record(client):
    payload = b"verification payload"
    upload_response = client.post(
        "/add_document",
        data={"file": (io.BytesIO(payload), "verify.txt")},
        content_type="multipart/form-data",
    )
    document_hash = upload_response.get_json()["document_hash"]

    client.get("/mine_block")
    verify_response = client.get(f"/verify_document/{document_hash}")

    assert verify_response.status_code == 200
    verify_data = verify_response.get_json()
    assert verify_data["verified"] is True
    assert verify_data["document"]["file_name"] == "verify.txt"


def test_upload_requires_non_empty_file(client):
    response = client.post(
        "/add_document",
        data={"file": (io.BytesIO(b""), "empty.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Uploaded file is empty."
