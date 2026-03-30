"""SQLite persistence layer for document and blockchain data."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DOCUMENT_COLUMNS = (
    "id",
    "document_hash",
    "document_name",
    "issuer",
    "owner",
    "document_type",
    "issued_at",
    "submitted_at",
    "file_name",
    "content_type",
    "file_size",
)


class BlockchainRepository:
    """Persist blockchain blocks and uploaded documents in SQLite."""

    def __init__(self, database_path):
        self.database_path = Path(database_path)
        if self.database_path.parent and not self.database_path.parent.exists():
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_index INTEGER NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    proof INTEGER NOT NULL,
                    previous_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_hash TEXT NOT NULL,
                    document_name TEXT,
                    issuer TEXT,
                    owner TEXT,
                    document_type TEXT,
                    issued_at TEXT,
                    submitted_at TEXT NOT NULL,
                    file_name TEXT,
                    content_type TEXT,
                    file_size INTEGER,
                    file_data BLOB,
                    status TEXT NOT NULL CHECK(status IN ('pending', 'mined')),
                    block_id INTEGER,
                    FOREIGN KEY(block_id) REFERENCES blocks(id)
                );
                """
            )

    def load_blocks(self):
        """Return persisted blocks with their mined documents."""
        with self._connect() as connection:
            block_rows = connection.execute(
                """
                SELECT id, block_index, timestamp, proof, previous_hash
                FROM blocks
                ORDER BY block_index ASC
                """
            ).fetchall()

            blocks = []
            for block_row in block_rows:
                document_rows = connection.execute(
                    """
                    SELECT id,
                           document_hash,
                           document_name,
                           issuer,
                           owner,
                           document_type,
                           issued_at,
                           submitted_at,
                           file_name,
                           content_type,
                           file_size
                    FROM documents
                    WHERE block_id = ?
                    ORDER BY id ASC
                    """,
                    (block_row["id"],),
                ).fetchall()
                blocks.append(
                    {
                        "index": block_row["block_index"],
                        "timestamp": block_row["timestamp"],
                        "proof": block_row["proof"],
                        "previous_hash": block_row["previous_hash"],
                        "documents": [self._document_from_row(row) for row in document_rows],
                    }
                )
            return blocks

    def load_pending_documents(self):
        """Return documents waiting to be mined."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id,
                       document_hash,
                       document_name,
                       issuer,
                       owner,
                       document_type,
                       issued_at,
                       submitted_at,
                       file_name,
                       content_type,
                       file_size
                FROM documents
                WHERE status = 'pending'
                ORDER BY id ASC
                """
            ).fetchall()
            return [self._document_from_row(row) for row in rows]

    def insert_document(self, document_record, file_bytes):
        """Persist a pending document and return the stored record."""
        values = (
            document_record["document_hash"],
            document_record.get("document_name"),
            document_record.get("issuer"),
            document_record.get("owner"),
            document_record.get("document_type"),
            document_record.get("issued_at"),
            document_record["submitted_at"],
            document_record.get("file_name"),
            document_record.get("content_type"),
            document_record.get("file_size"),
            file_bytes,
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO documents (
                    document_hash,
                    document_name,
                    issuer,
                    owner,
                    document_type,
                    issued_at,
                    submitted_at,
                    file_name,
                    content_type,
                    file_size,
                    file_data,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                values,
            )
            document_id = cursor.lastrowid
            row = connection.execute(
                """
                SELECT id,
                       document_hash,
                       document_name,
                       issuer,
                       owner,
                       document_type,
                       issued_at,
                       submitted_at,
                       file_name,
                       content_type,
                       file_size
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
            return self._document_from_row(row)

    def persist_block(self, block, document_ids):
        """Persist a mined block and attach pending documents to it."""
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.execute(
                """
                INSERT INTO blocks (block_index, timestamp, proof, previous_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    block["index"],
                    block["timestamp"],
                    block["proof"],
                    block["previous_hash"],
                ),
            )
            block_id = cursor.lastrowid
            for document_id in document_ids:
                connection.execute(
                    """
                    UPDATE documents
                    SET status = 'mined', block_id = ?
                    WHERE id = ?
                    """,
                    (block_id, document_id),
                )

    def _document_from_row(self, row):
        document = {}
        for column in DOCUMENT_COLUMNS:
            document[column] = row[column]
        return document
