"""
dsa package initialization.
Exports core custom data structures and the Document data model.
"""

from .document import Document
from .hash_map import CustomHashMap
from .folder_tree import TreeNode, FolderTree
from .merge_sort import custom_merge_sort

__all__ = [
    "Document",
    "CustomHashMap",
    "TreeNode",
    "FolderTree",
    "custom_merge_sort"
]
