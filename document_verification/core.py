"""Core blockchain logic for the document verification service."""

import datetime
import hashlib
import json

POW_PREFIX = "0000"
POW_PREFIX_LENGTH = len(POW_PREFIX)

OPTIONAL_DOCUMENT_FIELDS = (
    "document_name",
    "issuer",
    "owner",
    "document_type",
    "issued_at",
)


class Blockchain:
    """Manage a simple in-memory blockchain with queued document records."""

    def __init__(self):
        """Initialize the blockchain with a genesis block."""
        self.chain = []
        self.pending_documents = []
        self.create_block(proof=1, previous_hash="0", documents=[])

    def create_block(self, proof, previous_hash, documents=None):
        """Create a block, append it to the chain, and return it."""
        block = {
            "index": len(self.chain) + 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "proof": proof,
            "previous_hash": previous_hash,
            "documents": list(documents or []),
        }
        self.chain.append(block)
        return block

    def get_previous_block(self):
        """Return the most recently added block."""
        return self.chain[-1]

    def add_document(self, payload):
        """Queue a document record to be mined into the next block."""
        document_hash = str(payload["document_hash"]).strip()
        document = {
            "document_hash": document_hash,
            "submitted_at": datetime.datetime.now().isoformat(),
        }
        for field in OPTIONAL_DOCUMENT_FIELDS:
            value = payload.get(field)
            if value is not None and str(value).strip():
                document[field] = str(value).strip()
        self.pending_documents.append(document)
        return document

    def get_pending_documents(self):
        """Return a copy of the pending document queue."""
        return list(self.pending_documents)

    def mine_pending_documents(self):
        """Mine all pending documents into a new block."""
        previous_block = self.get_previous_block()
        previous_proof = previous_block["proof"]
        proof = self.proof_of_work(previous_proof)
        previous_hash = self.hash(previous_block)
        documents = self.get_pending_documents()
        block = self.create_block(proof, previous_hash, documents=documents)
        self.pending_documents = []
        return block

    def verify_document(self, document_hash):
        """Return matching document details if the hash exists on-chain."""
        target_hash = document_hash.strip()
        for block in self.chain:
            for document in block.get("documents", []):
                if document.get("document_hash") == target_hash:
                    return {
                        "verified": True,
                        "message": "Document exists on the blockchain.",
                        "block_index": block["index"],
                        "timestamp": block["timestamp"],
                        "document": document,
                    }
        return {
            "verified": False,
            "message": "Document hash not found on the blockchain.",
        }

    def proof_of_work(self, previous_proof):
        """Find a proof value that satisfies the current difficulty rule."""
        new_proof = 1
        previous_proof_squared = previous_proof ** 2
        while True:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof_squared).encode()
            ).hexdigest()
            if hash_operation[:POW_PREFIX_LENGTH] == POW_PREFIX:
                return new_proof
            new_proof += 1

    @staticmethod
    def hash(block):
        """Return the SHA-256 hash of a block."""
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        """Check whether a chain is structurally valid."""
        if not chain:
            return False

        previous_block = chain[0]
        if "documents" not in previous_block or not isinstance(
            previous_block["documents"], list
        ):
            return False

        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if "documents" not in block or not isinstance(block["documents"], list):
                return False
            if block["previous_hash"] != self.hash(previous_block):
                return False
            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(
                str(proof ** 2 - previous_proof ** 2).encode()
            ).hexdigest()
            if hash_operation[:POW_PREFIX_LENGTH] != POW_PREFIX:
                return False
            previous_block = block
            block_index += 1
        return True
