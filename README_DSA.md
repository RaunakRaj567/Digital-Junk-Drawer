# 🧠 Digital Junk Drawer: Data Structures & Algorithms (DSA) Specification

Welcome to the **Data Structures and Algorithms (DSA)** documentation for **Digital Junk Drawer**—an ML-powered intelligent document organization engine.

This project implements three fundamental computer science data structures from scratch in Python (without using Python's built-in `dict` for the HashMap or built-in `sorted()` for the sorting engine) and coordinates them through a unified `DocumentManager`.

---

## 🏛️ 1. System Architecture Overview

```
                          ┌────────────────────────┐
                          │   Incoming Document    │
                          │ (filename, size, path) │
                          └───────────┬────────────┘
                                      │
                                      ▼
                          ┌────────────────────────┐
                          │     ML Classifier      │
                          │   (Naive Bayes Model)  │
                          └───────────┬────────────┘
                                      │ Predicted Category
                                      ▼
                        ┌───────────────────────────┐
                        │      DocumentManager      │
                        │    (Central Controller)   │
                        └─────┬───────────────┬─────┘
                              │               │
            ┌─────────────────┴─┐           ┌─┴─────────────────┐
            ▼                   ▼           ▼                   ▼
    ┌───────────────┐   ┌───────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │ CustomHashMap │   │  FolderTree   │ │  CustomMergeSort  │ │    REST / CLI     │
    │  O(1) Access  │   │  Hierarchy    │ │   O(N log N)      │ │     API-Ready     │
    │  by doc_id    │   │  by Category  │ │  Multi-Key Sort   │ │    Operations     │
    └───────────────┘   └───────────────┘ └───────────────────┘ └───────────────────┘
```

---

## 🗄️ 2. Component 1: Custom HashMap (`dsa/hash_map.py`)

### 2.1 Purpose & Motivation
In a system managing thousands of documents, linear search ($O(N)$) by Document ID causes severe latency. The `CustomHashMap` provides **near-instantaneous $O(1)$ average time complexity** for insertions, lookups, updates, and deletions.

### 2.2 Core Architectural Elements
1. **Array-Based Storage**: A fixed-capacity list of buckets (initially `capacity = 16`).
2. **Polynomial Rolling Hash Function**:
   Computes a uniform integer bucket index from any string key:
   $$\text{hash}(s) = \left( \sum_{i=0}^{L-1} s[i] \cdot 31^{L-1-i} \right) \pmod{\text{capacity}}$$
   The prime multiplier $31$ minimizes hash clustering for alphanumeric keys.
3. **Collision Handling via Separate Chaining**:
   Each bucket holds a singly linked list of `HashNode` objects:
   ```
   Bucket[i] -> [ Node(key1, doc1) ] -> [ Node(key2, doc2) ] -> None
   ```
4. **Dynamic Resizing & Rehashing**:
   - Monitored by the **Load Factor**:
     $$\alpha = \frac{\text{size}}{\text{capacity}}$$
   - When $\alpha \ge 0.75$, `_resize(capacity * 2)` doubles the array size and rehashes all existing nodes to guarantee short bucket chains and optimal performance.

### 2.3 Operations & Time/Space Complexities

| Operation | Method | Average Time | Worst Time | Space | Notes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Insert** | `insert(key, value)` | $O(1)$ amortized | $O(N)$ | $O(1)$ | Inserts at head of chain or updates |
| **Retrieve** | `retrieve(key)` / `search` | $O(1)$ | $O(N)$ | $O(1)$ | Traverses bucket chain |
| **Update** | `update(key, value)` | $O(1)$ | $O(N)$ | $O(1)$ | Updates value in-place |
| **Delete** | `delete(key)` | $O(1)$ | $O(N)$ | $O(1)$ | Unlinks node from chain |
| **Resize** | `_resize(new_cap)` | $O(N)$ | $O(N)$ | $O(N)$ | Triggered only when $\alpha \ge 0.75$ |

> **Worst-Case Explanation**: $O(N)$ worst-case occurs if a malicious input causes every single key to hash to the exact same bucket. Dynamic resizing and the polynomial rolling hash make this scenario practically negligible.

---

## 🌳 3. Component 2: Custom Folder Tree (`dsa/folder_tree.py`)

### 3.1 Purpose & Motivation
Real-world file systems are naturally hierarchical. The `FolderTree` models the document organization where files belong to logical major folders (`Business`, `Tech`, `Politics`, `Sports`, `Entertainment`) and supports dynamic creation of custom folders.

### 3.2 Structure
```
Digital Junk Drawer (Root Node)
├── Business (Category Node)
│   ├── [DOC_1002] Tesla_Earnings.xlsx (Document Leaf Node)
│   └── [DOC_1007] Stock_Market_Data.csv (Document Leaf Node)
├── Tech
│   ├── [DOC_1004] Neural_Network_GPU.py
│   └── [DOC_1009] Apple_iOS_Update.zip
├── Politics
├── Sports
└── Entertainment
```

### 3.3 Node Representation (`TreeNode`)
- `name`: Human-readable identifier.
- `node_type`: `'root'`, `'category'`, or `'document'`.
- `document`: Reference to the `Document` object (if leaf node).
- `parent`: Pointer to parent node (enables moving between folders).
- `children`: List of child nodes.

### 3.4 Key Operations
- **`create_category(name)`**: Adds a category folder under root ($O(C)$ where $C$ is category count).
- **`insert_document(category, doc)`**: Inserts a leaf node under the category ($O(1)$ once category node is resolved).
- **`move_document(doc_id, new_category)`**: 
  1. Locates document node via DFS.
  2. Unlinks from old category parent.
  3. Relinks to new category parent.
  4. Synchronously updates `doc.category`.
- **`display_hierarchy()`**: Generates an ASCII visual tree using box-drawing characters (`├──`, `└──`, `│`).
- **`dfs()`**: Depth-First Search pre-order generator yielding every node in the hierarchy.

---

## 🔀 4. Component 3: Custom Merge Sort (`dsa/merge_sort.py`)

### 4.1 Purpose & Motivation
Users need to view documents sorted by various criteria (A-Z, largest file, newest upload). Merge Sort is chosen because:
1. **Guaranteed $O(N \log N)$ Performance**: Unlike QuickSort, Merge Sort never degrades to $O(N^2)$ on sorted or reverse-sorted inputs.
2. **Strict Stability**: Preserves the original relative order of documents with equal sorting keys.

### 4.2 Algorithm Workflow
1. **Divide**: Split list into left and right halves at midpoint `mid = len // 2`.
2. **Conquer**: Recursively call `custom_merge_sort()` on both halves until base case (`len <= 1`).
3. **Combine (`_merge`)**: Two pointers `i` and `j` traverse `left` and `right`. The smaller element is appended to `merged`.
   - **Stability Condition**: When `left_val == right_val`, the element from `left` is chosen first:
     ```python
     if not reverse:
         if left_val <= right_val:  # '<=' preserves stability!
             merged.append(left[i]); i += 1
         else:
             merged.append(right[j]); j += 1
     ```

### 4.3 Supported Sorting Keys & Modes

| Sort Key | Attribute Compared | Ascending (`reverse=False`) | Descending (`reverse=True`) |
| :--- | :--- | :--- | :--- |
| `'filename'` | Case-insensitive string | Alphabetical (A $\rightarrow$ Z) | Reverse (Z $\rightarrow$ A) |
| `'file_size'` | Integer byte count | Smallest $\rightarrow$ Largest | Largest $\rightarrow$ Smallest |
| `'upload_timestamp'` | Floating point seconds | Oldest $\rightarrow$ Newest | Newest $\rightarrow$ Oldest |

### 4.4 Complexity Analysis
- **Time Complexity**:
  - **Best Case**: $O(N \log N)$
  - **Average Case**: $O(N \log N)$
  - **Worst Case**: $O(N \log N)$
- **Space Complexity**:
  - **Auxiliary Space**: $O(N)$ for merged temporary arrays.
  - **Call Stack Depth**: $O(\log N)$ frames.

---

## 🔗 5. Integration: `DocumentManager` (`document_manager.py`)

The `DocumentManager` unifies the ML classifier and all three DSA structures:

```python
from document_manager import DocumentManager

# 1. Initialize
dm = DocumentManager()

# 2. Upload Document: ML predicts 'Sports', HashMap stores it, Tree indexes it
doc = dm.upload_document("champions_league_final.mp4", file_size=125000000)

# 3. Fast O(1) Retrieval by ID via HashMap
retrieved = dm.get_document_by_id(doc.doc_id)

# 4. Manual Category Re-Classification (HashMap & Tree stay in sync!)
dm.move_document_category(doc.doc_id, "Entertainment")

# 5. Stably Sort Documents across the drawer or within a category
sorted_docs = dm.sort_documents(sort_by="file_size", reverse=True)

# 6. Visual Tree Rendering
print(dm.display_tree())
```

---

## 🖥️ 6. Graphical User Interface (GUI) (`gui.py`)

The application features a tailored **two-page interactive desktop GUI** that mirrors the exact user workflow:

```bash
python gui.py
```

### 📥 Page 1: Unorganized Files Inbox (`sample_unorganized_files`)
1. **Live Detection**: Automatically scans and displays all files waiting in `sample_unorganized_files/` (showing Filename, Type, Size, and Date Modified).
2. **File Addition & Right-Click Copy**:
   - **`➕ Upload / Add Files to Inbox` Button**: Native file picker to copy new files directly into `sample_unorganized_files/`.
   - **`📁 Open 'sample_unorganized_files' in Explorer` Button**: Opens the physical directory so users can drag & drop or paste files directly from Windows Explorer.
   - **Right-Click Context Menu**: Right-click any file to copy its name to the clipboard instantly!
   - **`🔄 Refresh Inbox Table` Button**: Refreshes the view when files are added externally.
3. **Automated Arrangement**:
   - **`⚡ Proceed to Arrange into Organised Folders` Button**:
     - Runs the pre-trained Machine Learning model on each file/folder.
     - Predicts the major category (`Business`, `Tech`, `Politics`, `Sports`, `Entertainment`).
     - Moves/copies the files into their respective subfolders in `organized_files_output/`.
     - Indexes each document in the **Custom HashMap** (calculating its Document ID & Hash-Code) and inserts it into the **Custom FolderTree**.
4. **Page Transition**:
   - **`📂 View Organised Folders (New Page) ➔` Button**: Transitions to Page 2.

---

### 📂 Page 2: Organised Folders Explorer
1. **Dual Search Capabilities (Global Multi-Folder File Search)**:
   - **Folder Search Bar**: Search any folder name (e.g. `Sports`, `Tech`, `Business`, `Politics`, `Entertainment`) to display its properties card and **Folder Hash-Code** (`0x001F [Bucket 31]`).
   - **Live File Search Across ANY Folder**: Instant real-time filtering as you type that searches across **all folders** (global scope)! Finding files by keyword, extension (`.pdf`, `.xlsx`, `.mp4`), or Doc ID surfaces matching files from any category with their respective category badges and folder paths.
2. **Right-Click Context Menu on Files**:
   - Right-click any row in the file table (including global search results) to reveal a context menu:
     - 📋 **Copy Filename** (copies exact filename to clipboard)
     - 🆔 **Copy Document ID** (copies Doc ID to clipboard)
     - 🔑 **Copy Hash-Code** (copies document polynomial hash-code to clipboard)
     - ℹ️ **View Full Properties** (opens metadata dialog)
3. **Interactive Clickable Folders**:
   - Clickable folder cards for `Business`, `Tech`, `Politics`, `Sports`, `Entertainment`, and `All Folders`.
   - Clicking any folder opens it, loads its properties, and filters the table to show all files inside that specific folder.
4. **Custom Merge Sort Engine**:
   - **Sort By**: `Filename`, `Date of Upload`, or `File Size`.
   - **Order**: `Ascending (A-Z / Min / Old)` or `Descending (Z-A / Max / New)`.
   - **`Sort Files (Merge Sort)` Button**: Executes custom recursive Merge Sort in $O(N \log N)$ time and re-renders the table with execution timing.
5. **Document Table**:
   - Displays: `Doc ID`, `Filename`, `Folder / Category`, `File Size`, `Type`, `Upload Date`, and **`Document Hash-Code`**.
6. **Real-Time HashMap Diagnostics**:
   - Bottom status bar continuously displays the internal state of the Custom HashMap: Stored elements ($N$), Array capacity ($M$), Load factor ($\alpha$), Collisions, and Max chain length.

---

## 🌐 7. Eye-Catching HTML/CSS/JS Web Interface (`app.py` / `web_app.py`)

In addition to the native desktop GUI, we have built a **modern, eye-catching Web Application** powered by Flask with HTML5, CSS3, and JavaScript:

```bash
python app.py
```
*(Automatically opens your default web browser at `http://127.0.0.1:5000`)*

### Key Features of the Web Interface:
- **Modern Glassmorphism & Animations**: Deep indigo/slate gradient background, glowing borders, smooth card transitions, and vibrant category badges.
- **Drag-and-Drop File Uploads**: Drag and drop any files directly into the browser to upload them into `sample_unorganized_files`.
- **Global Cross-Folder File Search**:
  - Live search input allows searching files of **any folder via filename**, extension, or ID.
  - Search Scope selector lets users switch between `🌐 Search Across ALL Folders` (default) and `📁 Active Folder Only`.
  - Dynamically updates the folder properties card to summarize matching items, cumulative file sizes, and list of matching folders.
- **Folder Search & Properties**: Search any folder name to reveal its **Polynomial Hash-Code**, total file size, and file type breakdown.
- **Interactive Folder Cards**: Clickable animated cards for each folder with live item counters.
- **Custom Merge Sort**: Interactive dropdowns for sorting by Filename, Date of Upload, or File Size (Ascending / Descending) powered by the backend Merge Sort algorithm.
- **Full JavaScript Right-Click Context Menu**:
  - Right-clicking any file row opens a custom floating menu:
    - 📋 **Copy Filename** (copies to system clipboard using `navigator.clipboard.writeText`)
    - 🆔 **Copy Document ID**
    - 🔑 **Copy Hash-Code**
    - ℹ️ **View Full Properties**
  - Displays animated Toast Notifications (e.g. *"📋 Copied filename: 'Tesla_Report.xlsx'"*).
- **Live Custom HashMap Diagnostics**: Real-time metric pills showing HashMap size, capacity, load factor, and collisions.

---

## 🧪 8. Testing & Verification

The project includes an automated test suite ([`test_dsa.py`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/test_dsa.py)) with **24 unit tests** covering:
- HashMap collision chaining & dynamic resizing
- Tree insertion, category creation, moving, and deletion
- Merge Sort multi-key stability, ascending/descending, and edge cases
- Cross-folder multi-category file search
- Cross-structure state synchronization

### Running the Desktop GUI:
```bash
python gui.py
```

### Running Unit Tests:
```bash
python -m unittest test_dsa.py -v
```

### Running the CLI Demonstration:
```bash
python demo.py
```

---

## 🛡️ 7. Edge Cases Handled

1. **Hash Collisions**: Handled cleanly with unbounded separate chaining nodes without data loss.
2. **Rehashing Preservation**: All existing keys survive dynamic array doubling.
3. **Non-Existent Keys**: Methods like `get_document_by_id('INVALID')` return `None` safely without crashing.
4. **Empty Lists in Sorting**: Merge Sort handles `[]` and single-element lists without index errors.
5. **Cross-Structure Deletion**: Deleting a document removes it cleanly from both the HashMap bucket and the FolderTree category.
