"""
dsa/document.py
Defines the Document entity used throughout Digital Junk Drawer.
"""

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any


class Document:
    """
    Represents a single document stored and indexed within Digital Junk Drawer.

    Attributes:
    -----------
    doc_id : str
        Unique identifier for the document (e.g., 'DOC_001').
    filename : str
        Base name of the file (e.g., 'QuarterlyReport_2024.xlsx').
    file_path : str
        Absolute or relative path to the physical file.
    file_size : int
        Size of the file in bytes.
    upload_timestamp : float
        POSIX timestamp (seconds since epoch) when the file was added.
    category : str
        Assigned category (e.g., 'Business', 'Tech', 'Politics', 'Sports', 'Entertainment').
    file_type : str
        Extension or MIME type of the file (e.g., 'xlsx', 'pdf', 'mp4').
    """

    def __init__(
        self,
        doc_id: str,
        filename: str,
        file_path: str = "",
        file_size: int = 0,
        upload_timestamp: Optional[float] = None,
        category: str = "Unassigned",
        file_type: str = ""
    ):
        self.doc_id = str(doc_id)
        self.filename = str(filename)
        self.file_path = str(file_path) if file_path else filename
        self.file_size = int(file_size)
        self.upload_timestamp = float(upload_timestamp if upload_timestamp is not None else time.time())
        self.category = str(category).strip()

        # Derive file_type from filename if not explicitly provided
        if not file_type:
            _, ext = os.path.splitext(self.filename)
            self.file_type = ext.lstrip(".").lower() if ext else "unknown"
        else:
            self.file_type = file_type.lstrip(".").lower()

    @property
    def formatted_size(self) -> str:
        """Returns file size in human-readable format (B, KB, MB, GB)."""
        bytes_val = float(self.file_size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0 or unit == "TB":
                return f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
            bytes_val /= 1024.0
        return f"{self.file_size} B"

    @property
    def formatted_timestamp(self) -> str:
        """Returns upload timestamp in ISO 8601-like string format."""
        return datetime.fromtimestamp(self.upload_timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the document metadata into a dictionary."""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_formatted": self.formatted_size,
            "upload_timestamp": self.upload_timestamp,
            "upload_time_formatted": self.formatted_timestamp,
            "category": self.category,
            "file_type": self.file_type
        }

    def __repr__(self) -> str:
        return (
            f"Document(id={self.doc_id!r}, name={self.filename!r}, "
            f"cat={self.category!r}, size={self.formatted_size}, type={self.file_type!r})"
        )

    def __str__(self) -> str:
        return (
            f"[{self.doc_id}] {self.filename} ({self.file_type.upper()}, {self.formatted_size}) "
            f"-> {self.category} | Uploaded: {self.formatted_timestamp}"
        )
