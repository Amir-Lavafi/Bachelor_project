import time
import hashlib

class User:
    """Represents a user in the Bitcoin simulation."""
    def __init__(self, name):
        self.name = name
        self.wallet = Wallet(self)

    def __repr__(self):
        return self.name

class Wallet:
    """Represents a user's wallet with a public address and balance."""
    # A helper dictionary to map addresses back to user names for clarity in the simulation.
    # Moved here from Transaction class for better code organization.
    _address_to_name_map = {}

    def __init__(self, owner):
        self.owner = owner
        # Generate a simple pseudo-public address from the owner's name
        self.address = '1x' + hashlib.sha256(owner.name.encode()).hexdigest()[:10]
        self.balance = 100.0  # Initial balance for simulation purposes
        # Register the wallet automatically upon creation.
        Wallet.register_wallet(self)

    def __repr__(self):
        return f"Wallet for {self.owner.name} (Address: {self.address})"

    @staticmethod
    def register_wallet(wallet):
        """Stores a wallet's address and owner's name for easy lookup."""
        Wallet._address_to_name_map[wallet.address] = wallet.owner.name

    @staticmethod
    def get_owner_name_from_address(address):
        """Retrieves an owner's name from a given wallet address."""
        return Wallet._address_to_name_map.get(address, "Unknown")


class Transaction:
    """Represents a single transaction between a sender and a receiver."""
    def __init__(self, sender_wallet, receiver_wallet, amount):
        if sender_wallet.balance < amount:
            raise ValueError("Insufficient funds for this transaction.")
        self.sender_address = sender_wallet.address
        self.receiver_address = receiver_wallet.address
        self.amount = amount
        self.timestamp = time.time()
        # Create a unique string based on transaction data BEFORE creating the ID.
        # This resolves the AttributeError caused by a circular dependency where __init__ called __repr__
        # before the transaction_id was created.
        transaction_data_string = f"{self.sender_address}{self.receiver_address}{self.amount}{self.timestamp}"
        self.transaction_id = hashlib.sha256(transaction_data_string.encode()).hexdigest()

        # Update balances immediately upon creation
        sender_wallet.balance -= amount
        receiver_wallet.balance += amount

    def __repr__(self):
        return (f"Transaction({self.transaction_id[:6]}...): "
                f"{self.sender_address[:8]}... ({Wallet.get_owner_name_from_address(self.sender_address)}) -> "
                f"{self.receiver_address[:8]}... ({Wallet.get_owner_name_from_address(self.receiver_address)}) | "
                f"Amount: {self.amount} BTC")


def main():
    """Main function to run the simulation."""
    print("--- Public Bitcoin Transaction Simulation (No Mixer) ---")

    # 1. Create Users
    # Wallets are now automatically registered when a User is created.
    alice = User("Alice")
    bob = User("Bob")
    charlie = User("Charlie")
    david = User("David")
    users = [alice, bob, charlie, david]

    public_ledger = []

    print("\nInitial User Wallets:")
    for user in users:
        print(f"- {user.name}: {user.wallet.balance:.2f} BTC (Address: {user.wallet.address})")

    # 2. Users create public transactions
    print("\n--- Executing Transactions ---")

    try:
        # Alice sends 10 BTC to Charlie
        tx1 = Transaction(alice.wallet, charlie.wallet, 10.0)
        public_ledger.append(tx1)
        print(f"Transaction successful: Alice sent 10 BTC to Charlie.")

        # Bob sends 5 BTC to David
        tx2 = Transaction(bob.wallet, david.wallet, 5.0)
        public_ledger.append(tx2)
        print(f"Transaction successful: Bob sent 5 BTC to David.")
        
        # David sends 15 BTC to Alice
        tx3 = Transaction(david.wallet, alice.wallet, 15.0)
        public_ledger.append(tx3)
        print(f"Transaction successful: David sent 15 BTC to Alice.")

    except ValueError as e:
        print(f"Transaction failed: {e}")

    # 3. Review the public ledger
    print("\n--- Final Public Ledger (Traceable) ---")
    print("An adversary looking at this ledger can directly link senders to receivers.")
    for tx in public_ledger:
        print(tx)

    print("\n--- Final User Balances ---")
    for user in users:
        print(f"- {user.name}: {user.wallet.balance:.2f} BTC")
        
    print("\nSimulation complete. The transaction history is clear and public.")

if __name__ == "__main__":
    main()

