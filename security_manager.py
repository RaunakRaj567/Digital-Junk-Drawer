"""
security_manager.py
Backend Cryptographic Security Vault for Digital Junk Drawer.

Location of Stored Hashcode:
    c:\\Users\\Lenovo\\Desktop\\DSA Project\\security_vault.json

Features:
- Stores SHA-256 hashcode of the master folder password ("Ron567")
- Constant-time hash verification via hmac.compare_digest (prevents timing attacks)
- Session state tracking (LOCKED / UNLOCKED)
- Detailed cryptographic payload for UI hashing animation
"""

import os
import json
import hashlib
import hmac
from datetime import datetime

VAULT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "security_vault.json")
DEFAULT_TARGET_PASSWORD = "Ron567"
DEFAULT_HASH = hashlib.sha256(DEFAULT_TARGET_PASSWORD.encode("utf-8")).hexdigest()

class SecurityVaultManager:
    def __init__(self, vault_path=VAULT_FILE):
        self.vault_path = vault_path
        self.is_unlocked = False
        self._ensure_vault_exists()

    def _ensure_vault_exists(self):
        """Ensures the backend security_vault.json exists with valid hashcode."""
        if not os.path.exists(self.vault_path):
            data = {
                "vault_name": "Digital Junk Drawer Secure Folder Vault",
                "vault_path": "security_vault.json",
                "status": "LOCKED",
                "hash_algorithm": "SHA-256",
                "stored_hashcode": DEFAULT_HASH,
                "target_password_reference": DEFAULT_TARGET_PASSWORD,
                "description": "Backend cryptographic vault storing the SHA-256 hashcode for organized folders protection.",
                "created_at": datetime.now().isoformat(),
                "last_unlocked_at": None,
                "failed_attempts": 0,
                "successful_unlocks": 0
            }
            with open(self.vault_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def _load_vault(self):
        self._ensure_vault_exists()
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "stored_hashcode": DEFAULT_HASH,
                "status": "LOCKED"
            }

    def _save_vault(self, data):
        try:
            with open(self.vault_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving vault: {e}")

    def compute_hash(self, password: str) -> str:
        """Computes SHA-256 cryptographic hashcode of the plaintext password."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def verify_password(self, input_password: str) -> dict:
        """
        Computes the hash of input_password and matches against stored_hashcode in security_vault.json.
        Returns a rich payload for UI animation and verification.
        """
        vault_data = self._load_vault()
        stored_hash = vault_data.get("stored_hashcode", DEFAULT_HASH)
        
        input_hash = self.compute_hash(input_password)
        
        # Constant-time string comparison to prevent timing side-channel attacks
        matched = hmac.compare_digest(input_hash.lower(), stored_hash.lower())
        
        timestamp = datetime.now().isoformat()
        
        if matched:
            self.is_unlocked = True
            vault_data["status"] = "UNLOCKED"
            vault_data["last_unlocked_at"] = timestamp
            vault_data["successful_unlocks"] = vault_data.get("successful_unlocks", 0) + 1
            self._save_vault(vault_data)
            
            return {
                "success": True,
                "matched": True,
                "input_password_length": len(input_password),
                "input_hash": input_hash,
                "stored_hash": stored_hash,
                "algorithm": "SHA-256",
                "vault_location": "security_vault.json",
                "message": "✓ Hashcode matched perfectly! Access granted."
            }
        else:
            self.is_unlocked = False
            vault_data["status"] = "LOCKED"
            vault_data["failed_attempts"] = vault_data.get("failed_attempts", 0) + 1
            self._save_vault(vault_data)
            
            return {
                "success": False,
                "matched": False,
                "input_password_length": len(input_password),
                "input_hash": input_hash,
                "stored_hash": stored_hash,
                "algorithm": "SHA-256",
                "vault_location": "security_vault.json",
                "message": "❌ Try again, hashcode didn't match!"
            }

    def lock(self):
        """Re-locks the organized folder vault."""
        self.is_unlocked = False
        vault_data = self._load_vault()
        vault_data["status"] = "LOCKED"
        self._save_vault(vault_data)

    def get_status(self) -> dict:
        """Returns the current lock status and vault metadata."""
        vault_data = self._load_vault()
        return {
            "is_unlocked": self.is_unlocked,
            "status": "UNLOCKED" if self.is_unlocked else "LOCKED",
            "vault_file": "security_vault.json",
            "absolute_vault_path": os.path.abspath(self.vault_path),
            "stored_hashcode": vault_data.get("stored_hashcode", DEFAULT_HASH),
            "algorithm": "SHA-256",
            "failed_attempts": vault_data.get("failed_attempts", 0),
            "successful_unlocks": vault_data.get("successful_unlocks", 0)
        }

# Global singleton instance
vault_manager = SecurityVaultManager()
