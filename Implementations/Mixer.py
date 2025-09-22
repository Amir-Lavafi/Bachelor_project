import random
import time
import hashlib
import itertools

class User:
    """Represents a user in the Bitcoin simulation."""
    def __init__(self, name):
        self.name = name
        self.wallet = Wallet(self)

    def __repr__(self):
        return self.name

class Wallet:
    """Represents a user's wallet with a public address and balance."""
    def __init__(self, owner):
        self.owner = owner
        # Generate a simple pseudo-public address from the owner's name
        self.address = '1x' + hashlib.sha256(owner.name.encode()).hexdigest()[:10]
        self.balance = 100.0  # Initial balance for simulation purposes

    def __repr__(self):
        return f"Wallet for {self.owner.name} (Address: {self.address})"

class Transaction:
    """Represents a single transaction between a sender and a receiver."""
    def __init__(self, sender_wallet, receiver_address, amount):
        self.sender_address = sender_wallet.address
        self.receiver_address = receiver_address
        self.amount = amount
        self.timestamp = time.time()
        # Create a unique string based on transaction data BEFORE creating the ID.
        # This resolves the AttributeError caused by a circular dependency where __init__ called __repr__
        # before the transaction_id was created.
        transaction_data_string = f"{self.sender_address}{self.receiver_address}{self.amount}{self.timestamp}"
        self.transaction_id = hashlib.sha256(transaction_data_string.encode()).hexdigest()

    def __repr__(self):
        return (f"Transaction({self.transaction_id[:6]}...): "
                f"{self.sender_address[:8]}... -> {self.receiver_address[:8]}... | Amount: {self.amount} BTC")

class Mixer:
    """A simple Bitcoin mixer to anonymize transactions."""
    def __init__(self):
        self.pool_address = 'mixer_pool_address'
        # Add an 'address' attribute for duck-typing compatibility with the Wallet class.
        # This allows the Transaction constructor to access mixer.address just like it would wallet.address.
        self.address = self.pool_address
        self.pending_transactions = []
        self.ledger = []

    def add_transaction_to_pool(self, transaction):
        """Adds a user's transaction to the mixing pool."""
        print(f"\n[Mixer] Received {transaction.amount} BTC from {transaction.sender_address[:8]}... for mixing.")
        self.pending_transactions.append(transaction)
        # Simulate receiving the funds
        transaction.sender_wallet.balance -= transaction.amount
        print(f"[Wallet] {transaction.sender_wallet.owner.name}'s balance updated: {transaction.sender_wallet.balance:.2f} BTC")

    def mix_and_send(self, all_wallets):
        """Mixes and sends the funds from the pool to the intended recipients."""
        print("\n[Mixer] Starting mixing process...")
        random.shuffle(self.pending_transactions)
        time.sleep(1) # Simulate the time delay in mixing

        for tx in self.pending_transactions:
            # The mixer sends the money, not the original user.
            # The Transaction constructor now correctly uses the mixer's address due to the duck-typing fix.
            mixed_tx = Transaction(self, tx.receiver_address, tx.amount)

            # Find the recipient's wallet and update balance
            recipient_wallet = next((w for w in all_wallets if w.address == tx.receiver_address), None)
            if recipient_wallet:
                recipient_wallet.balance += tx.amount
                self.ledger.append(mixed_tx)
                print(f"[Mixer] Sent {tx.amount} BTC to {tx.receiver_address[:8]}... on behalf of an anonymous user.")
                print(f"[Wallet] {recipient_wallet.owner.name}'s balance updated: {recipient_wallet.balance:.2f} BTC")
            else:
                print(f"[Mixer] Error: Recipient wallet {tx.receiver_address} not found.")

        self.pending_transactions = [] # Clear the pool
        return self.ledger

def main():
    """Main function to run the simulation."""
    print("--- Bitcoin Transaction Simulation with a Mixer ---")

    # 1. Create Users
    alice = User("Alice")
    bob = User("Bob")
    charlie = User("Charlie")
    david = User("David")
    users = [alice, bob, charlie, david]
    wallets = [u.wallet for u in users]

    print("\nInitial User Wallets:")
    for user in users:
        print(f"- {user.name}: {user.wallet.balance:.2f} BTC (Address: {user.wallet.address})")

    # Store initial state for later analysis
    initial_balances = {u.name: u.wallet.balance for u in users}

    # 2. Create a Mixer
    mixer = Mixer()

    # 3. Users decide to send money and use the mixer
    # Alice sends 10 BTC to Charlie
    tx1 = Transaction(alice.wallet, charlie.wallet.address, 10.0)
    tx1.sender_wallet = alice.wallet # Attach wallet for balance update
    mixer.add_transaction_to_pool(tx1)

    # Bob sends 5 BTC to David
    tx2 = Transaction(bob.wallet, david.wallet.address, 5.0)
    tx2.sender_wallet = bob.wallet
    mixer.add_transaction_to_pool(tx2)

    # David sends 15 BTC to Alice
    tx3 = Transaction(david.wallet, alice.wallet.address, 15.0)
    tx3.sender_wallet = david.wallet
    mixer.add_transaction_to_pool(tx3)
    
    # Store transaction amounts for analysis
    tx_amounts = [tx1.amount, tx2.amount, tx3.amount]

    # 4. Mixer processes the transactions
    mixed_ledger = mixer.mix_and_send(wallets)

    # 5. Review the final ledger
    print("\n--- Final Public Ledger (Post-Mixing) ---")
    print("An adversary looking at this ledger cannot directly link the original senders to receivers.")
    print("All transactions appear to originate from the mixer's address.")
    for tx in mixed_ledger:
        print(tx)

    print("\n--- Final User Balances ---")
    for user in users:
        print(f"- {user.name}: {user.wallet.balance:.2f} BTC")

    print("\nSimulation complete. The link between (Alice -> Charlie), (Bob -> David), and (David -> Alice) is obscured.")

    # 6. NEW: Run the privacy analysis to find possible transaction scenarios
    final_balances = {u.name: u.wallet.balance for u in users}
    analyze_mixer_privacy(initial_balances, final_balances, tx_amounts, users)

def analyze_mixer_privacy(initial_balances, final_balances, tx_amounts, users):
    """
    Analyzes the mixer's effectiveness by finding all possible transaction mappings
    that could result in the observed balance changes.
    """
    print("\n--- Mixer Privacy Analysis ---")
    print("Attempting to deduce who paid whom based on initial/final balances and transaction amounts.")

    num_tx = len(tx_amounts)
    user_names = [u.name for u in users]
    
    # Store solutions as frozensets of tuples to easily find unique scenarios
    unique_solutions = set()

    # The adversary doesn't know the order of transactions, so we test every permutation of the amounts.
    # Using set() to get unique permutations in case of duplicate amounts.
    amount_permutations = list(set(itertools.permutations(tx_amounts)))
    print(f"Checking {len(amount_permutations)} unique permutation(s) of transaction amounts...")

    def find_solutions_recursive(tx_index, current_balances, path, ordered_amounts):
        """A recursive function to explore all sender/receiver assignments."""
        # Base case: if all transactions have been assigned
        if tx_index == num_tx:
            # Check if the final state matches the actual final balances
            if all(abs(current_balances[name] - final_balances[name]) < 1e-9 for name in user_names):
                # Add the found path as a frozenset to handle transaction order invariance
                unique_solutions.add(frozenset(path))
            return

        amount = ordered_amounts[tx_index]

        # Iterate through all possible senders and receivers for the current transaction
        for sender in users:
            for receiver in users:
                if sender == receiver:
                    continue

                # Create a hypothetical new state
                new_balances = current_balances.copy()
                new_balances[sender.name] -= amount
                new_balances[receiver.name] += amount

                # Recurse to the next transaction
                new_path = path + [(f"{sender.name} -> {receiver.name}", amount)]
                find_solutions_recursive(tx_index + 1, new_balances, new_path, ordered_amounts)

    # For each permutation of transaction amounts, run the solver
    for p in amount_permutations:
        find_solutions_recursive(0, initial_balances.copy(), [], p)

    if not unique_solutions:
        print("\nNo possible transaction scenarios found.")
    else:
        print(f"\nFound {len(unique_solutions)} possible unique scenario(s) that match the balance changes:")
        
        # Ground truth for comparison
        original_txs_set = frozenset([("Alice -> Charlie", 10.0), ("Bob -> David", 5.0), ("David -> Alice", 15.0)])
        
        for i, solution_frozenset in enumerate(unique_solutions):
            print(f"\n--- Scenario {i + 1} ---")
            # Sort for consistent printing
            solution_list = sorted(list(solution_frozenset), key=lambda x: x[1])
            for transaction, amount in solution_list:
                print(f"  - A transaction of {amount:.2f} BTC could be: {transaction}")
            
            if solution_frozenset == original_txs_set:
                print("  (This scenario matches the actual transactions that occurred)")
            
    print("\nAnalysis complete. If multiple scenarios are listed, the adversary cannot be certain which one is correct.")


if __name__ == "__main__":
    main()

