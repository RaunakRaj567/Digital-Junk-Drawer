"""
dsa/merge_sort.py
Custom recursive, stable Merge Sort algorithm implemented from scratch.

Sorting Capabilities:
1. Filename         : Alphabetical ascending and descending
2. File Size        : Smallest to largest and largest to smallest
3. Upload Timestamp : Oldest to newest and newest to oldest

IMPORTANT:
Does NOT use Python's built-in sorted() or list.sort().
"""

from typing import List, Callable, Any, Union
from .document import Document


def _extract_key(doc: Document, sort_key: Union[str, Callable[[Document], Any]]) -> Any:
    """
    Helper function to safely extract comparison key from a Document object.
    
    Supported string keys:
    - 'filename'          : Case-insensitive filename
    - 'file_size' / 'size': File size in integer bytes
    - 'upload_timestamp' / 'timestamp' / 'date' / 'upload_date': Upload epoch float
    - 'doc_id' / 'id'     : Document ID
    - 'category'          : Document category
    """
    if callable(sort_key):
        return sort_key(doc)

    key_str = str(sort_key).lower().strip()
    if key_str in ("filename", "name"):
        return doc.filename.lower()
    elif key_str in ("file_size", "size", "filesize"):
        return doc.file_size
    elif key_str in ("upload_timestamp", "timestamp", "upload_date", "date"):
        return doc.upload_timestamp
    elif key_str in ("doc_id", "id"):
        return str(doc.doc_id)
    elif key_str == "category":
        return doc.category.lower()
    elif key_str in ("file_type", "type"):
        return doc.file_type.lower()
    else:
        raise ValueError(f"Unsupported sorting key: {sort_key!r}. "
                         f"Choose from 'filename', 'file_size', 'upload_timestamp', 'category', 'doc_id'.")


def _merge(
    left: List[Document],
    right: List[Document],
    sort_key: Union[str, Callable[[Document], Any]],
    reverse: bool
) -> List[Document]:
    """
    Merges two sorted lists 'left' and 'right' into a single sorted list.
    
    Stability:
    ----------
    When left_val == right_val, the element from 'left' is ALWAYS chosen first.
    This guarantees that the algorithm is STABLE (preserving the relative order
    of identical elements from the original collection).
    """
    merged: List[Document] = []
    i = 0
    j = 0
    n_left = len(left)
    n_right = len(right)

    while i < n_left and j < n_right:
        left_val = _extract_key(left[i], sort_key)
        right_val = _extract_key(right[j], sort_key)

        if not reverse:
            # Ascending order: left element wins if <= right element (<= maintains stability)
            if left_val <= right_val:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1
        else:
            # Descending order: left element wins if >= right element (>= maintains stability)
            if left_val >= right_val:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

    # Append any remaining elements from left partition
    while i < n_left:
        merged.append(left[i])
        i += 1

    # Append any remaining elements from right partition
    while j < n_right:
        merged.append(right[j])
        j += 1

    return merged


def custom_merge_sort(
    documents: List[Document],
    sort_key: Union[str, Callable[[Document], Any]] = "filename",
    reverse: bool = False
) -> List[Document]:
    """
    Recursively sorts a list of Document objects using Merge Sort.

    Parameters:
    -----------
    documents : List[Document]
        List of Document objects to sort. Does not mutate the input list in-place.
    sort_key : str or Callable
        Attribute to sort by: 'filename', 'file_size', 'upload_timestamp', etc.
    reverse : bool
        If False, sorts in ascending order (A-Z, smallest to largest, oldest to newest).
        If True, sorts in descending order (Z-A, largest to smallest, newest to oldest).

    Returns:
    --------
    List[Document] : A new sorted list of Document objects.

    Time Complexity:
    ----------------
    - Best Case:    O(N log N)
    - Average Case: O(N log N)
    - Worst Case:   O(N log N)
    At every recursive level (log2 N levels), every element is compared and merged in O(N) time.

    Space Complexity:
    -----------------
    - Auxiliary Space: O(N) auxiliary space needed for merged subarrays.
    - Call Stack Space: O(log N) recursion depth.
    """
    # Base case: lists of size 0 or 1 are already sorted
    if len(documents) <= 1:
        return list(documents)

    # Divide: split the array into two halves at the midpoint
    mid = len(documents) // 2
    left_half = documents[:mid]
    right_half = documents[mid:]

    # Conquer: recursively sort both halves
    sorted_left = custom_merge_sort(left_half, sort_key=sort_key, reverse=reverse)
    sorted_right = custom_merge_sort(right_half, sort_key=sort_key, reverse=reverse)

    # Combine: merge the two sorted halves stably
    return _merge(sorted_left, sorted_right, sort_key=sort_key, reverse=reverse)
