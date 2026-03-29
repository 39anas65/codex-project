"""Minimal educational blockchain service built with Flask.

This script exposes a tiny in-memory blockchain with three HTTP endpoints:

- ``/mine_block`` mines and appends a new block
- ``/get_chain`` returns the full chain
- ``/is_valid`` validates the current chain

The implementation is intentionally simple and is meant for learning rather
than production use. Data is stored only in memory, proof-of-work difficulty
is fixed, and no peer-to-peer consensus is implemented.
"""

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify

# Part 1 - Building a Blockchain

POW_PREFIX = '0000'
POW_PREFIX_LENGTH = len(POW_PREFIX)

class Blockchain:
    """Manage a simple in-memory blockchain.

    The chain starts with a genesis block and supports creating new blocks,
    hashing blocks, validating chain integrity, and computing a basic
    proof-of-work value.
    """

    def __init__(self):
        """Initialize the blockchain with a genesis block."""
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0')

    def create_block(self, proof, previous_hash):
        """Create a block, append it to the chain, and return it.

        Args:
            proof: Proof-of-work value for the new block.
            previous_hash: Hash of the previous block in the chain.

        Returns:
            A dictionary representing the newly created block.
        """
        block = {'index': len(self.chain) + 1,
                 'timestamp': datetime.datetime.now().isoformat(),
                 'proof': proof,
                 'previous_hash': previous_hash}
        self.chain.append(block)
        return block

    def get_previous_block(self):
        """Return the most recently added block."""
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        """Find a proof value that satisfies the current difficulty rule.

        The rule used here is intentionally basic: hash the expression
        ``new_proof**2 - previous_proof**2`` and require the resulting
        hexadecimal digest to start with ``POW_PREFIX``.

        Args:
            previous_proof: Proof value stored in the previous block.

        Returns:
            An integer proof satisfying the proof-of-work condition.
        """
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
        """Return the SHA-256 hash of a block.

        The block is serialized with sorted keys to ensure deterministic
        hashing across calls.

        Args:
            block: Block dictionary to hash.

        Returns:
            A hexadecimal SHA-256 digest string.
        """
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        """Check whether a chain is structurally valid.

        Validation confirms both of the following for every block after the
        genesis block:

        1. ``previous_hash`` matches the hash of the prior block.
        2. The stored proof satisfies the proof-of-work rule.

        Args:
            chain: List of block dictionaries to validate.

        Returns:
            ``True`` when the chain is valid, otherwise ``False``.
        """
        if not chain:
            return False

        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof ** 2 - previous_proof ** 2).encode()
            ).hexdigest()
            if hash_operation[:POW_PREFIX_LENGTH] != POW_PREFIX:
                return False
            previous_block = block
            block_index += 1
        return True

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating a Blockchain
blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    """Mine a new block and return its contents."""
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']}
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])
def get_chain():
    """Return the full blockchain and its current length."""
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def is_valid():
    """Return whether the current blockchain passes validation checks."""
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Running the app
if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
