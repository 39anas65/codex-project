# Document Verification Blockchain

This project is an educational document verification service built with Flask,
an in-memory blockchain, and a Streamlit UI. Users can upload documents,
compute composite document hashes from file content plus metadata, mine pending
records into blocks, inspect the chain, and verify whether a document
fingerprint exists on-chain.

The codebase is intentionally lightweight and readable. It is designed for
learning and demos rather than for production use.

## Demo

![Demo](./browser-test-recording.mp4)

## Features

- in-memory blockchain with a genesis block
- basic proof-of-work mining
- block hashing with SHA-256
- document record queue for pending submissions
- document verification against mined blocks
- Flask HTTP API for blockchain and document workflows
- Streamlit UI for local interaction without manual API calls

## Project Files

- `blockchain.py`: runnable Flask backend entrypoint
- `document_verification/core.py`: blockchain and document queue logic
- `document_verification/api.py`: Flask routes and request handling
- `streamlit_app.py`: Streamlit user interface
- `SPEC.md`: product specification for the MVP

## Setup With uv

```bash
uv sync --dev
```

## Run Locally

1. Start the Flask backend:

```bash
uv run python blockchain.py
```

2. In a separate terminal, start the Streamlit UI:

```bash
uv run streamlit run streamlit_app.py
```

3. Open the applications:

- Flask API: `http://127.0.0.1:5000`
- Streamlit UI: `http://localhost:8501`

If `uv` is not installed yet, install it first from the official Astral
instructions: `https://docs.astral.sh/uv/getting-started/installation/`

## Run Tests

```bash
uv run pytest
```

## API Endpoints

### `GET /mine_block`

Mines a new block containing all pending document records.

### `GET /get_chain`

Returns the full blockchain and its length.

### `GET /is_valid`

Checks whether the blockchain is valid.

### `POST /add_document`

Queues a document record to be included in the next block.

Request format:

- `multipart/form-data`
- required file field: `document_file`
- optional text fields: `document_name`, `issuer`, `owner`, `document_type`,
  `issued_at`, `document_summary`

The backend computes `document_hash` automatically from the uploaded file and
the provided metadata, and assigns `submitted_at` on the server.

### `GET /pending_documents`

Returns all pending document records waiting to be mined.

### `GET /verify_document/<document_hash>`

Checks whether a document hash exists in any mined block.

## Notes

- data is not persisted and resets when the server restarts
- mining difficulty is fixed and intentionally simple
- duplicate document hashes are allowed for this MVP
- there is no peer-to-peer networking, consensus, or authentication
- this repository is for learning and experimentation
