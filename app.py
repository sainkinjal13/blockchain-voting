import hashlib
import json
import re
import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==========================================
# MOCK ELECTION CARD REGISTRY DATABASE
# ==========================================
# These are mock, structurally valid Election Cards (3 Letters + 7 Digits)
MOCK_GOVERNMENT_DB = [
    "XYZ1234567",
    "DLH9876543",
    "PUN5554443",
    "MAH0001112"
]

# ==========================================
# BLOCKCHAIN ENGINE CONFIGURATION
# ==========================================
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class VotingBlockchain:
    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.voted_identifiers = set()  # Stores SHA256 hashes of Voter IDs to prevent double voting
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def add_vote(self, raw_id, candidate):
        # 1. Structural Format Check (EPIC Standard: 3 Uppercase Letters followed by 7 Digits)
        cleaned = str(raw_id).replace(" ", "").replace("-", "").upper()
        if not re.match(r"^[A-Z]{3}[0-9]{7}$", cleaned):
            return False, "Invalid Election Card format. Must match standard layout like 'XYZ1234567'."

        # 2. Database Registration Check
        if cleaned not in MOCK_GOVERNMENT_DB:
            return False, "This Election Card Number is not registered in the electoral roll database."

        # 3. Double Voting Prevention (Anonymized Fingerprint Check)
        hashed_voter = hashlib.sha256(cleaned.encode()).hexdigest()
        if hashed_voter in self.voted_identifiers:
            return False, "Fraud Alert: This Election Card identity has already cast a vote!"

        # 4. Save to Block Pool
        vote = {"voter_hash": hashed_voter, "candidate": candidate, "timestamp": time.time()}
        self.unconfirmed_transactions.append(vote)
        self.voted_identifiers.add(hashed_voter)
        
        # Mine instantly to update the blockchain ledger
        self.mine()
        return True, "Identity verified. Vote successfully securely stored on the Blockchain!"

    def mine(self):
        if not self.unconfirmed_transactions:
            return False
        new_block = Block(index=self.chain[-1].index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=self.chain[-1].hash)
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.unconfirmed_transactions = []
        return True

    def tally_votes(self):
        results = {"Candidate A": 0, "Candidate B": 0, "Candidate C": 0}
        for block in self.chain[1:]:
            for vote in block.transactions:
                cand = vote['candidate']
                results[cand] = results.get(cand, 0) + 1
        return results

# Initialize Blockchain Instance
election_blockchain = VotingBlockchain()

# ==========================================
# WEB CONTROLLER ROUTING
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    data = request.json
    id_number = data.get('id_number')
    candidate = data.get('candidate')

    if not id_number or not candidate:
        return jsonify({"success": False, "message": "Missing card inputs or candidate selection."}), 400

    success, message = election_blockchain.add_vote(id_number, candidate)
    return jsonify({"success": success, "message": message})

@app.route('/results', methods=['GET'])
def get_results():
    results = election_blockchain.tally_votes()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)