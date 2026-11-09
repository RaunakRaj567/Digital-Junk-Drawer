"""
demo.py
Interactive and complete demonstration script for Digital Junk Drawer.

Demonstrates:
1. Uploading 12 realistic documents across diverse categories, file types, and sizes.
2. Automated Machine Learning category prediction.
3. Fast O(1) storage and retrieval using Custom HashMap.
4. Hierarchical folder organization and visual tree rendering using Custom FolderTree.
5. Manual re-classification and cross-structure synchronization.
6. Custom recursive Merge Sort across multiple keys and directions (filename, size, date).
7. Document deletion and cleanup.
8. Diagnostic statistics of custom DSA structures.
9. Edge cases (duplicate names, non-existent keys, empty category sorts).
"""

import sys
import time
from document_manager import DocumentManager

# Reconfigure stdout for utf-8 if supported on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)


def print_doc_table(docs, title: str):
    print(f"\n--- {title} ({len(docs)} documents) ---")
    print(f"{'Doc ID':<10} | {'Filename':<42} | {'Category':<15} | {'Size':<10} | {'Uploaded'}")
    print("-" * 95)
    for d in docs:
        print(f"{d.doc_id:<10} | {d.filename:<42} | {d.category:<15} | {d.formatted_size:<10} | {d.formatted_timestamp}")
    print("-" * 95)


def main():
    print_banner("DIGITAL JUNK DRAWER: ML-POWERED INTELLIGENT DOCUMENT ORGANIZER")
    print("Initializing DocumentManager (Custom HashMap + Custom FolderTree + Custom MergeSort)...")
    
    manager = DocumentManager()
    stats = manager.get_system_stats()
    print(f"✓ ML Model Status : {'Loaded from .pkl' if stats['ml_model_loaded'] else 'Heuristic Engine'}")
    print(f"✓ Default Tree    : Initialized with {stats['categories_count']} major categories")
    print(f"✓ Custom HashMap  : Initial capacity {stats['hash_map_diagnostics']['capacity']} buckets")

    # =========================================================================
    # STEP 1: Uploading at least 10 realistic documents (12 items)
    # =========================================================================
    print_banner("STEP 1: Uploading 12 Documents with Automated ML Categorization")

    sample_uploads = [
        ("champions_league_football_final_highlights.mp4", 125000000),  # Sports (~125 MB)
        ("Tesla_Quarterly_Financial_Earnings_Report.xlsx", 2450000),     # Business (~2.4 MB)
        ("PresidentialElectionVotingResults2024.pdf", 890000),           # Politics (~890 KB)
        ("nvidia_rtx_gpu_neural_network_benchmarks.py", 45000),          # Tech (~45 KB)
        ("hollywood_movie_festival_award_winners.mkv", 450000000),       # Entertainment (~450 MB)
        ("cricket_world_cup_match_schedule.pdf", 320000),                # Sports (~320 KB)
        ("stock_market_inflation_and_bank_interest_rates.csv", 1500000), # Business (~1.5 MB)
        ("prime_minister_cabinet_press_conference.docx", 640000),        # Politics (~640 KB)
        ("apple_iphone_ios_firmware_update.zip", 85000000),              # Tech (~85 MB)
        ("grammy_awards_music_album_nominees.mp3", 9500000),             # Entertainment (~9.5 MB)
        ("nba_playoffs_lakers_vs_warriors_recap.mp4", 98000000),         # Sports (~98 MB)
        ("cybersecurity_ransomware_attack_prevention.pdf", 1200000)      # Tech (~1.2 MB)
    ]

    uploaded_docs = []
    for filename, size in sample_uploads:
        # Small delay to ensure distinct upload timestamps for sorting demonstration
        time.sleep(0.02)
        doc = manager.upload_document(filename=filename, file_size=size)
        uploaded_docs.append(doc)
        print(f"  [+] Uploaded: {doc.filename:<45} -> Predicted: 📂 {doc.category:<13} ({doc.formatted_size})")

    # =========================================================================
    # STEP 2: Display Folder Tree Hierarchy
    # =========================================================================
    print_banner("STEP 2: Custom FolderTree Hierarchy (ML-Sorted View)")
    print(manager.display_tree())

    # =========================================================================
    # STEP 3: O(1) Fast Document Retrieval via Custom HashMap
    # =========================================================================
    print_banner("STEP 3: O(1) Retrieval via Custom HashMap by Document ID")
    target_id = uploaded_docs[1].doc_id  # Tesla report
    retrieved = manager.get_document_by_id(target_id)
    print(f"Querying Document ID: '{target_id}'...")
    if retrieved:
        print("✓ Match found instantly via Custom HashMap:")
        for k, v in retrieved.to_dict().items():
            print(f"    - {k:<22}: {v}")

    # =========================================================================
    # STEP 4: Manual Re-Classification & Multi-Structure Synchronization
    # =========================================================================
    print_banner("STEP 4: Manual Category Re-Classification & State Sync")
    # Let's say user wants to move Tesla report from Business to Tech
    move_doc = uploaded_docs[1]
    print(f"Moving '{move_doc.filename}' [ID: {move_doc.doc_id}]")
    print(f"Current Category: {move_doc.category}")
    print("Action: User manually re-classifies to -> 'Tech'")

    success = manager.move_document_category(move_doc.doc_id, "Tech")
    print(f"Operation Success: {success}")

    # Verify synchronization in both HashMap and Tree
    synced_map_doc = manager.get_document_by_id(move_doc.doc_id)
    tech_tree_docs = manager.list_documents_in_category("Tech")
    print(f"✓ HashMap state updated category : {synced_map_doc.category}")
    print(f"✓ FolderTree Tech item count     : {len(tech_tree_docs)} documents")
    print(f"✓ Contains moved document in Tree : {any(d.doc_id == move_doc.doc_id for d in tech_tree_docs)}")

    # =========================================================================
    # STEP 5: Custom Merge Sort Demonstrations
    # =========================================================================
    print_banner("STEP 5: Custom Recursive Merge Sort Demonstrations")

    # 5.1 Sort by Filename (Alphabetical Ascending A-Z)
    sorted_alpha_asc = manager.sort_documents(sort_by="filename", reverse=False)
    print_doc_table(sorted_alpha_asc, "Merge Sort by Filename (Ascending: A-Z)")

    # 5.2 Sort by File Size (Largest to Smallest Descending)
    sorted_size_desc = manager.sort_documents(sort_by="file_size", reverse=True)
    print_doc_table(sorted_size_desc, "Merge Sort by File Size (Descending: Largest -> Smallest)")

    # 5.3 Sort by Upload Timestamp (Oldest to Newest)
    sorted_time_asc = manager.sort_documents(sort_by="upload_timestamp", reverse=False)
    print_doc_table(sorted_time_asc, "Merge Sort by Upload Date (Ascending: Oldest -> Newest)")

    # 5.4 Sort Within a Specific Category Folder (e.g. Sports by File Size)
    sports_by_size = manager.sort_documents(category="Sports", sort_by="file_size", reverse=False)
    print_doc_table(sports_by_size, "Merge Sort Within Category 'Sports' by File Size (Smallest -> Largest)")

    # =========================================================================
    # STEP 6: Document Deletion & Synchronization
    # =========================================================================
    print_banner("STEP 6: Deleting a Document and Verifying Tree & Map Clean-up")
    doc_to_delete = uploaded_docs[0]  # Champions league highlights
    del_id = doc_to_delete.doc_id
    print(f"Deleting document [{del_id}]: '{doc_to_delete.filename}'...")

    deleted = manager.delete_document(del_id)
    print(f"Deletion result: {deleted}")
    print(f"HashMap search after delete : {manager.get_document_by_id(del_id)}")
    sports_after = manager.list_documents_in_category("Sports")
    print(f"Sports category count after : {len(sports_after)} documents")

    # =========================================================================
    # STEP 7: Custom HashMap Internal Diagnostics
    # =========================================================================
    print_banner("STEP 7: Custom HashMap Internal Diagnostics (DSA Evaluation)")
    sys_stats = manager.get_system_stats()
    hash_stats = sys_stats["hash_map_diagnostics"]
    print(f"Total Stored Elements (N)  : {hash_stats['size']}")
    print(f"Bucket Array Capacity (M)  : {hash_stats['capacity']}")
    print(f"Current Load Factor (N/M)  : {hash_stats['load_factor']}")
    print(f"Non-Empty Buckets          : {hash_stats['non_empty_buckets']}")
    print(f"Total Collisions Handled   : {hash_stats['collisions']}")
    print(f"Maximum Bucket Chain Length: {hash_stats['max_chain_length']}")
    print("\nCategory Distribution in FolderTree:")
    for cat, count in sys_stats["categories"].items():
        print(f"  - 📂 {cat:<15}: {count} documents")

    # =========================================================================
    # STEP 8: Edge Cases and Resilience Handling
    # =========================================================================
    print_banner("STEP 8: Edge-Case Handling & Robustness")
    
    # 8.1 Retrieval of non-existent ID
    print("Testing non-existent document ID retrieval:")
    result = manager.get_document_by_id("DOC_99999")
    print(f"  get_document_by_id('DOC_99999') -> {result} (Handled gracefully)")

    # 8.2 Moving non-existent document
    print("\nTesting move of non-existent document:")
    move_result = manager.move_document_category("DOC_99999", "Tech")
    print(f"  move_document_category('DOC_99999', 'Tech') -> {move_result} (Handled safely)")

    # 8.3 Sorting an empty category
    print("\nTesting sorting on an empty category:")
    manager.tree.create_category("UnusedCategory")
    empty_sort = manager.sort_documents(category="UnusedCategory", sort_by="filename")
    print(f"  sort_documents('UnusedCategory') -> {empty_sort} (No crash, returns empty list)")

    print_banner("DEMONSTRATION COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
