# Document Verification Blockchain API Spec

## Overview

This project extends the existing educational Flask blockchain app into a small
document verification service. The application will allow users to register a
document fingerprint on-chain, mine pending records into blocks, and verify
later that a document or certificate has not been altered. It will also include
a lightweight Python-based user interface so users can interact with the system
without calling the HTTP API manually.

The app remains intentionally lightweight and educational:

- data is stored in memory
- no authentication is required for the MVP
- no peer-to-peer networking or distributed consensus is included
- proof-of-work remains simple and fixed-difficulty
- the UI should be built with Streamlit as a simple Python-first frontend layer

## Goals

- Demonstrate a practical blockchain use case beyond empty block mining
- Keep the codebase small and understandable for learning
- Expose clear HTTP APIs for adding, mining, listing, and verifying records
- Provide a simple UI for submitting and verifying document records
- Reuse the current `Blockchain` and Flask API structure as much as possible

## Non-Goals

- Production-grade security or persistence
- User accounts, login, or access control
- Smart contracts or cryptocurrency features
- File storage on the blockchain
- Multi-node synchronization or consensus between peers
- A complex frontend build pipeline based on JavaScript frameworks for the MVP

## Primary Use Case

A user wants to prove that a document existed in a specific state at a specific
time. The application stores the document's hash and metadata in a pending
queue. Once a block is mined, that record becomes part of the chain and can be
verified later by recomputing the hash and checking whether it exists on-chain.
The same user should also be able to perform these actions from a simple web UI
served by the Python application.

Example documents:

- course completion certificates
- internship certificates
- project completion records
- agreement PDFs
- academic transcripts

## Users

- students learning blockchain concepts
- developers exploring Flask APIs
- small demo teams building a proof of concept for notarization

## Functional Requirements

### 0. Provide a Python-based UI

The system must include a lightweight user interface implemented with a Pythonic
framework or pattern compatible with the current project.

Required MVP choice:

- Streamlit

Preferred approach for this repository:

- keep Flask as the backend API layer
- add a separate Streamlit app as the UI layer
- have Streamlit call the Flask endpoints for add, mine, verify, and chain
  views
- avoid introducing a JavaScript-heavy frontend for the MVP

The UI should allow users to:

- submit a document hash and metadata
- view pending document records
- mine a block
- verify a document hash
- inspect the current blockchain

### 1. Register a document record

The system must allow a client to submit a document record before mining.

Required fields:

- `document_hash`: SHA-256 hash of the document contents

Optional fields:

- `document_name`
- `issuer`
- `owner`
- `document_type`
- `issued_at`

Behavior:

- the record is added to a pending transactions/documents list
- the response confirms the record was queued successfully
- the chain is not modified until a block is mined

### 2. Mine pending document records

The system must mine a new block containing all currently pending document
records.

Behavior:

- perform proof-of-work using the current algorithm
- create a new block linked to the previous block hash
- include pending records in the block
- clear the pending list after successful block creation
- return the mined block in the response

### 3. Retrieve the blockchain

The system must return the full blockchain and chain length.

Behavior:

- preserve the existing `/get_chain` endpoint
- include each block's document records in the payload

### 4. Validate the blockchain

The system must confirm the blockchain is structurally valid.

Behavior:

- preserve the existing `/is_valid` endpoint
- validate previous hash linkage and proof-of-work
- return a simple valid/invalid response

### 5. Verify a document

The system must allow a client to check whether a given document hash exists in
the blockchain.

Behavior:

- search all mined blocks for a matching `document_hash`
- if found, return verification success with block details
- if not found, return verification failure

### 6. List pending records

The system should expose the current pending document queue for visibility.

Behavior:

- return all unmined document records
- return queue length

## Proposed API

### `GET /mine_block`

Mines all pending document records into a new block.

Success response:

```json
{
  "message": "Congratulations, you just mined a block!",
  "index": 2,
  "timestamp": "2026-03-29T11:00:00",
  "proof": 533,
  "previous_hash": "abc123...",
  "documents": [
    {
      "document_hash": "f1c9...",
      "document_name": "certificate.pdf",
      "issuer": "ABC Academy"
    }
  ]
}
```

### `GET /get_chain`

Returns the full chain and total length.

### `GET /is_valid`

Returns whether the blockchain is valid.

### `POST /add_document`

Queues a document record to be included in the next mined block.

Request body:

```json
{
  "document_hash": "f1c9d2...",
  "document_name": "certificate.pdf",
  "issuer": "ABC Academy",
  "owner": "John Doe",
  "document_type": "certificate",
  "issued_at": "2026-03-29"
}
```

Success response:

```json
{
  "message": "Document record added to pending queue.",
  "pending_count": 1
}
```

### `GET /pending_documents`

Returns all pending records waiting to be mined.

### `GET /verify_document/<document_hash>`

Checks whether a document hash exists in any mined block.

Success response:

```json
{
  "verified": true,
  "message": "Document exists on the blockchain.",
  "block_index": 2,
  "timestamp": "2026-03-29T11:00:00",
  "document": {
    "document_hash": "f1c9d2...",
    "document_name": "certificate.pdf",
    "issuer": "ABC Academy"
  }
}
```

Failure response:

```json
{
  "verified": false,
  "message": "Document hash not found on the blockchain."
}
```

## UI Specification

### Recommended Framework

The preferred UI implementation is:

- Streamlit

Reasoning:

- it keeps the project fully Python-based
- it is easier to understand for an educational repository
- it avoids unnecessary frontend build complexity
- it provides forms, tables, status messages, and layout primitives quickly

### Proposed Pages

#### Dashboard

Dashboard page showing:

- project title and short description
- current chain length
- number of pending documents
- quick actions for add, mine, verify, and view chain

Implementation notes:

- this can be the default Streamlit home view
- metrics can be shown using Streamlit summary components

#### Add Document

Form page for adding a document record.

Fields:

- `document_hash`
- `document_name`
- `issuer`
- `owner`
- `document_type`
- `issued_at`

Behavior:

- validates required fields
- submits to the backend
- shows a success or error message

#### Pending Documents

Page listing all pending document records waiting to be mined.

Behavior:

- fetch data from the Flask API
- display records in a table-like layout

#### Verify Document

Page with a form to input a document hash and display verification results.

Displayed result should include:

- verified or not verified state
- block index if found
- document metadata if found
- timestamp if found

#### Blockchain Explorer

Page displaying the blockchain in a readable format.

Each block view should show:

- block index
- timestamp
- proof
- previous hash
- document count
- document list

#### Mine Block

UI action that triggers mining and refreshes the displayed data with a success
message.

## UI Requirements

- the UI must be implemented in Streamlit
- the UI must be easy to run locally with a single Streamlit command
- styling should be simple, readable, and responsive enough for desktop and
  mobile screens
- the Streamlit app should be placed in a dedicated file such as `app.py` or
  `streamlit_app.py`
- if custom styling is added, it should be minimal and embedded cleanly in the
  Streamlit app
- API endpoints should remain available even after the UI is added

## UI and Backend Interaction

- Flask remains the blockchain API service
- Streamlit acts as the client-facing application
- Streamlit should communicate with Flask over HTTP on the local machine
- the UI should handle backend errors gracefully and show readable messages
- configuration should make the backend base URL easy to change for local runs

## Development Commands

Install dependencies:

```powershell
uv sync --dev
```

Run the backend API:

```powershell
uv run python blockchain.py
```

Run the Streamlit UI:

```powershell
uv run streamlit run streamlit_app.py
```

## Data Model

### Block

Each block should contain:

- `index`
- `timestamp`
- `proof`
- `previous_hash`
- `documents`

Example:

```json
{
  "index": 2,
  "timestamp": "2026-03-29T11:00:00",
  "proof": 533,
  "previous_hash": "abc123...",
  "documents": [
    {
      "document_hash": "f1c9d2...",
      "document_name": "certificate.pdf",
      "issuer": "ABC Academy",
      "owner": "John Doe",
      "document_type": "certificate",
      "issued_at": "2026-03-29"
    }
  ]
}
```

### Pending Document Record

Each pending record should contain:

- `document_hash` required
- optional metadata fields listed above
- `submitted_at` generated by the server

## Validation Rules

- `document_hash` is required
- `document_hash` must be a non-empty string
- duplicate hashes may be allowed for MVP, but the API should clearly return
  what happened
- empty mining requests should still be handled gracefully
- request bodies must be valid JSON for `POST /add_document`

## Error Handling

The API should return simple JSON error responses for invalid input.

Examples:

- missing `document_hash`
- malformed JSON request body
- unsupported HTTP method

Suggested format:

```json
{
  "error": "document_hash is required"
}
```

## MVP Implementation Plan

### Phase 1

- add a pending documents list to the `Blockchain` class
- update block creation to include documents
- add `add_document` method
- add `get_pending_documents` method
- add `verify_document` method
- add Flask routes for adding, listing, and verifying documents
- add a Streamlit UI for dashboard, add document, pending documents, verify,
  and chain views
- add backend integration from Streamlit to the Flask API
- add basic UI feedback for loading, success, and error states

### Phase 2

- add automated tests with `pytest`
- cover chain validation, mining behavior, and verification behavior
- test both success and failure API responses
- add lightweight tests for helper functions used by the Streamlit app where
  practical

## Future Enhancements

- persist chain data to a JSON or SQLite file
- upload a file and compute `document_hash` on the server
- reject duplicate documents automatically
- add issuer authentication
- add digital signatures for issuers
- add multiple nodes and consensus endpoints
- improve the Streamlit UI with document upload, search, filters, and status
  feedback

## Risks and Constraints

- all data is lost when the Flask server restarts
- the app does not guarantee distributed trust because it runs as a single node
- proof-of-work is educational only and not secure for real production use
- verification proves matching hash presence, not document ownership or legal validity

## Success Criteria

The MVP is successful when:

- a user can submit a document hash through the API
- a user can submit a document hash through the UI
- a mined block includes pending document records
- `/get_chain` shows document-bearing blocks
- `/verify_document/<document_hash>` correctly finds existing records
- the UI allows users to view the chain, pending records, and verification results
- `/is_valid` still confirms chain integrity after mining
