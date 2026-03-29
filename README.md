# Blockchain Learning Project

This project is a minimal educational blockchain service built with Flask. It
includes a small in-memory blockchain implementation and a simple HTTP API for
mining blocks, viewing the chain, and validating chain integrity.

The codebase is intentionally lightweight and easy to read. It is designed for
learning blockchain basics rather than for production use.

## Current Features

- in-memory blockchain with a genesis block
- basic proof-of-work mining
- block hashing with SHA-256
- chain validation
- Flask HTTP API

## API Endpoints

### `GET /mine_block`

Mines a new block and appends it to the chain.

### `GET /get_chain`

Returns the full blockchain and its length.

### `GET /is_valid`

Checks whether the blockchain is valid.

## Project Files

- `blockchain.py`: Flask app and blockchain implementation
- `SPEC.md`: planned product spec for extending this into a document
  verification blockchain application

## Run Locally

1. Create and activate a virtual environment if you want an isolated setup.
2. Install Flask:

```bash
pip install flask
```

3. Start the app:

```bash
python blockchain.py
```

4. Open the API in your browser or API client:

- `http://127.0.0.1:5000/mine_block`
- `http://127.0.0.1:5000/get_chain`
- `http://127.0.0.1:5000/is_valid`

## Notes

- data is not persisted and resets when the app restarts
- mining difficulty is fixed and intentionally simple
- there is no peer-to-peer networking or consensus
- this repository is for learning and experimentation

## Planned Direction

The repository also includes a specification for evolving the app into a
document verification blockchain service with:

- queued document records
- mined document history
- document verification endpoints
- a Streamlit-based user interface

See `SPEC.md` for the full roadmap.
