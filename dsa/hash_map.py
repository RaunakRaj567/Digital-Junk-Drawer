"""
dsa/hash_map.py
Custom HashMap implementation from scratch using array-based storage,
polynomial rolling hash function, separate chaining for collision resolution,
and automatic dynamic resizing (rehashing).

IMPORTANT:
Does NOT use Python's built-in dict or set for storage.
"""

from typing import Any, Optional, List, Tuple


class HashNode:
    """
    Node for separate chaining in the CustomHashMap.
    Forms a singly linked list in each bucket to store colliding key-value pairs.
    """
    def __init__(self, key: str, value: Any, next_node: Optional['HashNode'] = None):
        self.key: str = str(key)
        self.value: Any = value
        self.next: Optional['HashNode'] = next_node

    def __repr__(self) -> str:
        return f"HashNode({self.key!r} -> {self.value!r})"


class CustomHashMap:
    """
    A custom Hash Table implementation featuring:
    1. Fixed-size array (list of bucket heads).
    2. Polynomial rolling hash function for string keys.
    3. Collision resolution via Separate Chaining (singly linked list per bucket).
    4. Dynamic resizing (rehashing) when load factor >= threshold.
    5. Full CRUD operations (Insert, Retrieve, Update, Delete, Search).

    Time Complexity:
    ----------------
    - Insert (Average):  O(1) amortized
    - Insert (Worst):    O(N) if all keys hash to the same bucket (without resize)
    - Search (Average):  O(1)
    - Search (Worst):    O(N)
    - Delete (Average):  O(1)
    - Delete (Worst):    O(N)
    - Resize/Rehash:     O(N) performed infrequently when load factor exceeds threshold

    Space Complexity:
    -----------------
    - O(N + M), where N is number of stored key-value pairs and M is capacity of the bucket array.
    """

    DEFAULT_CAPACITY = 16
    DEFAULT_LOAD_FACTOR_THRESHOLD = 0.75
    POLYNOMIAL_BASE = 31

    def __init__(self, capacity: int = DEFAULT_CAPACITY, load_factor_threshold: float = DEFAULT_LOAD_FACTOR_THRESHOLD):
        """
        Initializes the hash map with a fixed initial capacity and load factor threshold.
        """
        if capacity <= 0:
            raise ValueError("Initial capacity must be greater than zero.")
        if not (0.1 <= load_factor_threshold <= 1.0):
            raise ValueError("Load factor threshold must be between 0.1 and 1.0.")

        self.capacity: int = capacity
        self.load_factor_threshold: float = load_factor_threshold
        self.size: int = 0
        
        # Array-based storage: list of bucket heads (initially all None)
        self.buckets: List[Optional[HashNode]] = [None] * self.capacity

    def _hash(self, key: str) -> int:
        """
        Custom hash function using polynomial rolling hash technique.
        Computes: hash = sum(ord(char) * base^(len - 1 - i)) mod capacity.
        
        This distributes ASCII / Unicode strings uniformly across buckets.
        """
        key_str = str(key)
        hash_value = 0
        for char in key_str:
            hash_value = (hash_value * self.POLYNOMIAL_BASE + ord(char)) % self.capacity
        return hash_value

    @property
    def load_factor(self) -> float:
        """Computes current load factor: size / capacity."""
        return self.size / self.capacity

    def _resize(self, new_capacity: int) -> None:
        """
        Resizes the bucket array to new_capacity and rehashes all existing entries.
        Ensures O(1) average lookup performance is maintained.
        """
        old_buckets = self.buckets
        self.capacity = new_capacity
        self.buckets = [None] * self.capacity
        self.size = 0  # Re-counted during re-insertion

        # Rehash all nodes from old buckets into new buckets
        for head in old_buckets:
            current = head
            while current is not None:
                self.insert(current.key, current.value)
                current = current.next

    def insert(self, key: str, value: Any) -> None:
        """
        Inserts a key-value pair into the hash map.
        If the key already exists, updates its value (In-place Update).
        Triggers automatic resizing if load factor exceeds threshold.
        """
        key_str = str(key)

        # Check if resize is required before inserting a new key
        if (self.size + 1) / self.capacity >= self.load_factor_threshold:
            self._resize(self.capacity * 2)

        bucket_index = self._hash(key_str)
        head = self.buckets[bucket_index]

        # Check if key already exists in this chain (Update)
        current = head
        while current is not None:
            if current.key == key_str:
                current.value = value
                return  # Updated existing key; size does not change
            current = current.next

        # Key does not exist; insert new node at the head of the chain (O(1) insertion)
        new_node = HashNode(key=key_str, value=value, next_node=head)
        self.buckets[bucket_index] = new_node
        self.size += 1

    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieves the value associated with the specified key.
        Returns None if key is not found.
        """
        key_str = str(key)
        bucket_index = self._hash(key_str)
        current = self.buckets[bucket_index]

        while current is not None:
            if current.key == key_str:
                return current.value
            current = current.next

        return None

    def search(self, doc_id: str) -> Optional[Any]:
        """
        Alias for retrieve. Searches for a document by its document ID.
        """
        return self.retrieve(doc_id)

    def update(self, key: str, value: Any) -> bool:
        """
        Updates an existing key with a new value.
        Returns True if key was found and updated, False otherwise.
        """
        key_str = str(key)
        bucket_index = self._hash(key_str)
        current = self.buckets[bucket_index]

        while current is not None:
            if current.key == key_str:
                current.value = value
                return True
            current = current.next

        return False

    def delete(self, key: str) -> bool:
        """
        Deletes the key-value pair associated with the given key.
        Returns True if the key was found and removed, False otherwise.
        """
        key_str = str(key)
        bucket_index = self._hash(key_str)
        current = self.buckets[bucket_index]
        prev: Optional[HashNode] = None

        while current is not None:
            if current.key == key_str:
                if prev is None:
                    # Node to delete is the head of the chain
                    self.buckets[bucket_index] = current.next
                else:
                    prev.next = current.next
                self.size -= 1
                return True
            prev = current
            current = current.next

        return False

    def contains(self, key: str) -> bool:
        """Checks if a key exists in the hash map."""
        return self.retrieve(key) is not None

    def keys(self) -> List[str]:
        """Returns a list of all keys currently in the hash map."""
        result = []
        for head in self.buckets:
            current = head
            while current is not None:
                result.append(current.key)
                current = current.next
        return result

    def values(self) -> List[Any]:
        """Returns a list of all values currently in the hash map."""
        result = []
        for head in self.buckets:
            current = head
            while current is not None:
                result.append(current.value)
                current = current.next
        return result

    def items(self) -> List[Tuple[str, Any]]:
        """Returns a list of all (key, value) tuples currently in the hash map."""
        result = []
        for head in self.buckets:
            current = head
            while current is not None:
                result.append((current.key, current.value))
                current = current.next
        return result

    def get_stats(self) -> dict:
        """
        Returns internal diagnostic statistics for DSA evaluation:
        - Capacity
        - Number of elements (size)
        - Current load factor
        - Non-empty buckets count
        - Number of collisions
        - Maximum chain length
        """
        non_empty = 0
        max_chain = 0
        total_collisions = 0

        for head in self.buckets:
            if head is not None:
                non_empty += 1
                chain_len = 0
                current = head
                while current is not None:
                    chain_len += 1
                    current = current.next
                if chain_len > 1:
                    total_collisions += (chain_len - 1)
                if chain_len > max_chain:
                    max_chain = chain_len

        return {
            "capacity": self.capacity,
            "size": self.size,
            "load_factor": round(self.load_factor, 4),
            "non_empty_buckets": non_empty,
            "collisions": total_collisions,
            "max_chain_length": max_chain
        }

    def __len__(self) -> int:
        return self.size

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def __getitem__(self, key: str) -> Any:
        val = self.retrieve(key)
        if val is None:
            raise KeyError(f"Key {key!r} not found in CustomHashMap.")
        return val

    def __setitem__(self, key: str, value: Any) -> None:
        self.insert(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.delete(key):
            raise KeyError(f"Key {key!r} not found in CustomHashMap.")

    def __repr__(self) -> str:
        return f"<CustomHashMap size={self.size} capacity={self.capacity} load_factor={self.load_factor:.2f}>"
