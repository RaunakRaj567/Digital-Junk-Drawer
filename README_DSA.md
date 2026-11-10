# 🧠 Digital Junk Drawer: Data Structures & Algorithms (DSA) Specification

**Digital Junk Drawer** is an ML-powered document organizer. You drop messy files into an inbox folder; a Naive Bayes model reads each **filename**, predicts its topic (Business, Tech, Politics, Sports, Entertainment), copies it into the matching folder, and indexes it in three data structures built **from scratch** in Python:

| Structure | File | Job in the project | Key complexity |
| :--- | :--- | :--- | :---: |
| **Custom HashMap** | [dsa/hash_map.py](dsa/hash_map.py) | Instant lookup of any document by its ID | $O(1)$ average |
| **Folder Tree (N-ary)** | [dsa/folder_tree.py](dsa/folder_tree.py) | Models the folder hierarchy; move/delete/visualize | $O(C)$ insert, $O(N)$ DFS |
| **Merge Sort** | [dsa/merge_sort.py](dsa/merge_sort.py) | Stable sorting by name, size or upload date | $O(N \log N)$ always |
| **SHA-256 Vault** | [security_manager.py](security_manager.py) | Password-locks the organized folders | $O(L)$ hash + constant-time compare |

The HashMap does **not** use Python's `dict` for storage and Merge Sort does **not** call `sorted()` / `list.sort()`. A central [document_manager.py](document_manager.py) keeps all structures in sync.

> 📘 The machine-learning side (dataset, TF-IDF, Naive Bayes, accuracy) is documented in [README_ML.md](README_ML.md).

---

## 📁 0. Project Layout

```
DSA Project/
├── dsa/
│   ├── document.py          # Document entity (id, name, path, size, timestamp, category, type)
│   ├── hash_map.py          # CustomHashMap + HashNode (separate chaining, rehashing)
│   ├── folder_tree.py       # FolderTree + TreeNode (N-ary tree, DFS, ASCII renderer)
│   └── merge_sort.py        # custom_merge_sort + stable _merge
├── document_manager.py      # Central controller: ML + HashMap + Tree + Sort + disk sync
├── ml_classifier.py         # Loads the .pkl model, cleans filenames, keyword fallback
├── security_manager.py      # SHA-256 vault lock for the organized folders
├── gui.py                   # Tkinter two-page desktop app
├── web_app.py / app.py      # Flask REST API + HTML/CSS/JS web app (templates/index.html)
├── demo.py                  # End-to-end CLI demonstration
├── test_dsa.py              # 24 unit + integration tests
├── text-classification-using-naive-bayes.ipynb   # Model training notebook
├── file_classifier_model.pkl / model.pkl / model_metadata.json
├── sample_unorganized_files/   # INBOX: drop messy files here
└── organized_files_output/     # OUTPUT: business/ entertainment/ politics/ sports/ tech/
```

---

## 🏛️ 1. System Architecture

```
   sample_unorganized_files/          (the "junk drawer" inbox)
              │  filename e.g. "Runs_Cricket.txt"
              ▼
   ┌──────────────────────┐   "runs cricket"   ┌──────────────────────────┐
   │ clean_filename_for_ml │ ────────────────▶ │ ML Classifier (TF-IDF +  │
   │ strip ext, split      │                   │ Multinomial Naive Bayes) │
   │ camelCase, drop _ - 0-9│                  └────────────┬─────────────┘
   └──────────────────────┘                                │ "Sports" (confidence %)
                                                            ▼
                                  ┌───────────────────────────────────────┐
                                  │           DocumentManager             │
                                  │  copies file → organized/sports/      │
                                  │  creates Document(DOC_1007, ...)      │
                                  └───┬──────────────┬──────────────┬─────┘
                                      ▼              ▼              ▼
                            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                            │CustomHashMap │ │  FolderTree  │ │  Merge Sort  │
                            │ DOC_1007 →   │ │ Root→Sports→ │ │ on demand:   │
                            │ Document     │ │ Runs_Cricket │ │ name/size/date│
                            └──────────────┘ └──────────────┘ └──────────────┘
                                      ▲
                     ┌────────────────┴────────────────┐
                     │  GUI (Tkinter)  /  Web (Flask)  │──▶ 🔐 SHA-256 Vault guards Page 2
                     └─────────────────────────────────┘
```

**Why two structures for the same documents?** They answer different questions fast:
- *"Give me DOC_1007"* → HashMap, $O(1)$.
- *"What's inside Sports?"* / *"Move this file to Tech"* / *"Draw the folder tree"* → Tree.

The `DocumentManager` is the single place that writes to both, so they never disagree.

---

## 🗄️ 2. Component 1: Custom HashMap ([dsa/hash_map.py](dsa/hash_map.py))

### 2.1 Why a HashMap?
Every document gets an ID like `DOC_1007`. Searching a plain list for an ID is $O(N)$. A hash table turns the ID into an array index directly, giving $O(1)$ average lookup.

### 2.2 Design

| Element | Implementation |
| :--- | :--- |
| **Storage** | Python list of bucket heads, `[None] * capacity`, initial `capacity = 16` |
| **Hash function** | Polynomial rolling hash, base **31**, Horner's method, `mod capacity` at every step |
| **Collision handling** | **Separate chaining**: each bucket is a singly linked list of `HashNode(key, value, next)` |
| **New-key insert** | At the **head** of the chain, $O(1)$ |
| **Resizing** | When $(size+1)/capacity \ge 0.75$, capacity **doubles** and every node is rehashed |

**Hash function** (from `_hash`):
```python
hash_value = 0
for char in key:
    hash_value = (hash_value * 31 + ord(char)) % self.capacity
```
which is equivalent to
$$h(s) = \left( \sum_{i=0}^{L-1} \text{ord}(s_i) \cdot 31^{\,L-1-i} \right) \bmod \text{capacity}$$

- **Why 31?** It is an odd prime, so multiplying spreads character values across buckets well (same constant as Java's `String.hashCode`).
- **Why mod at every step?** Keeps the intermediate number small; no huge integers for long filenames.

**Collision chain example:**
```
bucket[7] → [DOC_1001 | Document] → [DOC_1042 | Document] → None
```

**Load factor:**
$$\alpha = \frac{\text{size}}{\text{capacity}}, \qquad \text{resize when } \alpha \ge 0.75$$

### 2.3 Operations & Complexity

| Operation | Method | Average | Worst | Notes |
| :--- | :--- | :---: | :---: | :--- |
| Insert | `insert(key, value)` | $O(1)$ amortized | $O(N)$ | Updates value in place if key exists |
| Retrieve | `retrieve(key)` / `search(doc_id)` | $O(1)$ | $O(N)$ | Walks one bucket chain |
| Update | `update(key, value)` | $O(1)$ | $O(N)$ | Returns `False` if key missing |
| Delete | `delete(key)` | $O(1)$ | $O(N)$ | Unlinks node (handles head vs. middle) |
| Contains | `contains(key)` / `in` | $O(1)$ | $O(N)$ | |
| Resize | `_resize(2 * capacity)` | $O(N)$ | $O(N)$ | Rare, so insert stays $O(1)$ amortized |
| keys / values / items | | $O(N + M)$ | $O(N + M)$ | $M$ = capacity |

Space: $O(N + M)$.

**Amortized $O(1)$ insert:** doubling means each resize copies $N$ items, but it only happens after $N/2$ cheap inserts, so the average cost per insert is still constant.

**Worst case $O(N)$** happens only if every key lands in one bucket. Base-31 hashing plus doubling makes this very unlikely for real IDs (see the benchmark below: max chain length 5 at 100,000 keys).

Pythonic extras: `len(m)`, `key in m`, `m[key]`, `m[key] = v`, `del m[key]` all work through dunder methods.

### 2.4 Live diagnostics: `get_stats()`
Both UIs show these numbers in real time:
```python
{'capacity': 16, 'size': 11, 'load_factor': 0.6875,
 'non_empty_buckets': 11, 'collisions': 0, 'max_chain_length': 1}
```
(Actual output after organizing the 11 files in `sample_unorganized_files/`.)

### 2.5 Measured performance
Run on this project's code, Python 3.8, 100,000 document IDs:

| Measurement | Result |
| :--- | :--- |
| Average insert (including all resizes) | **≈ 6.9 µs** |
| Average lookup by ID | **≈ 1.2 µs** |
| Linear scan of a 100k list for the last ID (`list.index`, C-optimized) | **≈ 654 µs** |
| Final state | capacity 262,144 · load factor 0.38 · **max chain length 5** |

The custom HashMap lookup is about **500× faster** than a linear scan, even though the scan runs in C and the HashMap is pure Python.

### 2.6 Hash-codes in the UI
`DocumentManager.get_doc_hash_code()` shows the bucket a document lives in, e.g. `0x0007 [Bucket 7]` for `DOC_1001` at capacity 16. Folder cards show the hash-code of the folder name the same way (`Sports` → `0x000F [Bucket 15]`). Because the index is `mod capacity`, these codes change when the table resizes, which is a nice live demonstration of rehashing.

---

## 🌳 3. Component 2: Folder Tree ([dsa/folder_tree.py](dsa/folder_tree.py))

### 3.1 Why a Tree?
Folders are naturally hierarchical: one root, category folders below it, files as leaves. A tree lets us list a folder's contents, move a file between folders, and draw the hierarchy.

### 3.2 Structure: real `display_hierarchy()` output for the 11 sample files
```
📦 Digital Junk Drawer/ [Root Node | Total Categories: 5]      ← root
├── 📂 Business/ (4 items)                                      ← category node
│   ├── 📄 [DOC_1001] Drama_serial.txt (TXT, 0 B)               ← document (leaf) node
│   ├── 📄 [DOC_1003] Fundraise_society.txt (TXT, 0 B)
│   ├── 📄 [DOC_1006] Operating System.txt (TXT, 0 B)
│   └── 📄 [DOC_1010] Stock_2026.txt (TXT, 0 B)
├── 📂 Tech/ (1 items)
│   └── 📄 [DOC_1009] Software_malware.txt (TXT, 0 B)
├── 📂 Politics/ (2 items)
│   ├── 📄 [DOC_1002] EVM_vote_hack.txt (TXT, 0 B)
│   └── 📄 [DOC_1007] Party clash.txt (TXT, 0 B)
├── 📂 Sports/ (3 items)
│   ├── 📄 [DOC_1005] Olympics_Hockey.txt (TXT, 0 B)
│   ├── 📄 [DOC_1008] Runs_Cricket.txt (TXT, 0 B)
│   └── 📄 [DOC_1011] football fixture.txt (TXT, 0 B)
└── 📂 Entertainment/ (1 items)
    └── 📄 [DOC_1004] Movie_rating.txt (TXT, 0 B)
```
> `Drama_serial.txt` and `Operating System.txt` landing in Business is caused by the keyword fallback described in §10. With the model retrained in the current environment they go to **Entertainment** and **Tech** (see [README_ML.md §8](README_ML.md)).

### 3.3 `TreeNode`
| Field | Meaning |
| :--- | :--- |
| `name` | Folder name or filename |
| `node_type` | `'root'`, `'category'` or `'document'` |
| `document` | Reference to the `Document` (leaf nodes only) |
| `parent` | Pointer up the tree, needed to unlink a node when moving it |
| `children` | List of child nodes (N-ary, not binary) |

### 3.4 Operations & Complexity
$C$ = number of categories (5 by default), $N$ = total nodes, $k$ = files in one category.

| Operation | Method | Time | How |
| :--- | :--- | :---: | :--- |
| Create folder | `create_category(name)` | $O(C)$ | Checks for duplicates, then appends under root |
| Find folder | `search_category(name)` | $O(C)$ | Case-insensitive scan of root's children |
| Insert file | `insert_document(cat, doc)` | $O(C)$ | Finds/creates category, appends leaf, sets `doc.category` |
| List folder | `get_documents_in_category(cat)` | $O(C + k)$ | |
| Find file | `search_document_node(doc_id)` | $O(N)$ | DFS |
| Move file | `move_document(doc_id, cat)` | $O(N)$ | DFS to find → unlink from old parent → link to new parent → update `doc.category` |
| Delete file | `delete_document(doc_id)` | $O(N)$ | DFS + unlink |
| Traverse | `dfs()` | $O(N)$ | Recursive pre-order **generator** (yields lazily) |
| Draw | `display_hierarchy(cat=None)` | $O(N)$ | ASCII tree using `├──`, `└──`, `│` |
| Export | `get_tree_dict(cat=None)` | $O(N)$ | Nested dict for the web/GUI tree visualizer |

**Design note:** finding a file in the tree is $O(N)$, but the app rarely needs to, because the HashMap already gives $O(1)$ access by ID. Each structure handles what it is good at.

---

## 🔀 4. Component 3: Merge Sort ([dsa/merge_sort.py](dsa/merge_sort.py))

### 4.1 Why Merge Sort?
1. **Guaranteed $O(N \log N)$**: no bad inputs. QuickSort degrades to $O(N^2)$ on already-sorted data, and file lists are often already partly sorted.
2. **Stable**: files with equal keys (same size, say) keep their previous relative order, so sorting by date and then by size behaves the way a user expects.
3. **Non-mutating**: returns a new list; the HashMap/Tree contents are untouched.

### 4.2 Algorithm
1. **Divide**: `mid = len(docs) // 2`
2. **Conquer**: recursively sort both halves; base case `len <= 1`
3. **Combine** (`_merge`): two pointers `i`, `j`; take the smaller element each step, then append leftovers.

**The stability trick:** on a tie, always take from the **left** half:
```python
if not reverse:
    if left_val <= right_val:      # '<=' (not '<') keeps equal items in original order
        merged.append(left[i]); i += 1
    else:
        merged.append(right[j]); j += 1
else:
    if left_val >= right_val:      # descending, still left-first on ties
        ...
```
Descending order is handled **inside the comparison**, not by reversing the result afterwards (reversing would break stability).

### 4.3 Sort keys

| `sort_key` (aliases) | Compared value | Ascending | Descending (`reverse=True`) |
| :--- | :--- | :--- | :--- |
| `filename` / `name` | lowercase filename | A → Z | Z → A |
| `file_size` / `size` | bytes (int) | smallest → largest | largest → smallest |
| `upload_timestamp` / `date` | epoch seconds (float) | oldest → newest | newest → oldest |
| `doc_id` / `id`, `category`, `file_type` | string | | |
| any `callable` | `key(doc)` | | |

An unknown key raises a clear `ValueError`.

### 4.4 Complexity
| | Best | Average | Worst |
| :--- | :---: | :---: | :---: |
| **Time** | $O(N \log N)$ | $O(N \log N)$ | $O(N \log N)$ |
| **Space** | $O(N)$ auxiliary | | recursion depth $O(\log N)$ |

Recurrence: $T(N) = 2T(N/2) + O(N) \Rightarrow O(N \log N)$ ($\log_2 N$ levels, $O(N)$ merge work per level).

---

## 🔐 5. Component 4: SHA-256 Folder Vault ([security_manager.py](security_manager.py))

After files are arranged, the **Organised Folders** page is locked. To open it the user enters a password, and the app compares hashes rather than storing the password itself.

| Step | What happens |
| :--- | :--- |
| 1 | `security_vault.json` stores only the **SHA-256 digest** (64 hex chars) of the password |
| 2 | On unlock, the input is hashed: `hashlib.sha256(pwd.encode()).hexdigest()` |
| 3 | Digests are compared with `hmac.compare_digest`, a **constant-time** comparison that stops timing attacks from leaking how many characters matched |
| 4 | Vault records `status`, `failed_attempts`, `successful_unlocks`, `last_unlocked_at` |
| 5 | Running *Arrange* again **re-locks** the vault automatically |

The web UI shows an animated terminal comparing the input digest with the stored digest; the desktop GUI shows both digests in a dialog.

**Hashing vs. hash tables:** the HashMap uses a *fast, non-cryptographic* hash (base-31) to choose a bucket, where collisions are expected and handled. The vault uses a *cryptographic* hash (SHA-256), designed so that collisions and reversal are computationally infeasible. Same idea, different goal.

---

## 🔗 6. Integration: `DocumentManager` ([document_manager.py](document_manager.py))

```python
from document_manager import DocumentManager

dm = DocumentManager()

# Upload: ML predicts the category → HashMap.insert → Tree.insert_document
doc = dm.upload_document("champions_league_final.mp4", file_size=125_000_000)

dm.get_document_by_id(doc.doc_id)                       # O(1) via HashMap
dm.move_document_category(doc.doc_id, "Entertainment")  # Tree move + HashMap update
dm.sort_documents(sort_by="file_size", reverse=True)    # Merge Sort (all folders)
dm.sort_documents(category="Sports", sort_by="date")    # Merge Sort (one folder)
dm.search_by_name(".pdf")                               # search all folders by name / ID / type
dm.delete_document(doc.doc_id)                          # removed from BOTH structures
print(dm.display_tree())                                # ASCII tree
dm.get_system_stats()                                   # HashMap diagnostics + per-folder counts
```

**Batch pipeline**, `organize_from_unorganized_folder()`:
1. Reset HashMap and Tree; clear old files in `organized_files_output/<category>/`.
2. For each file **or sub-folder** in the inbox: predict the category → copy into `organized_files_output/<category>/` → `upload_document()`.
3. Return doc ID, category, confidence, bucket hash-code and destination for each item.

**Disk synchronization**, `sync_with_disk()`, runs before listing, sorting and searching:
- **Prune**: if a user deletes a file in Explorer, it is removed from the HashMap and Tree.
- **Auto-discover**: files found in `organized_files_output/<category>/` that aren't indexed yet are added (used at web-app start-up).

---

## 🖥️ 7. User Interfaces

### 7.1 Desktop GUI: `python gui.py` (Tkinter)

**Page 1: Unorganized Files Inbox**
- Live table of `sample_unorganized_files/` (name, type, size, modified date)
- **➕ Upload / Add Files**, **📁 Open in Explorer**, **🔄 Refresh**, right-click → copy filename
- **⚡ Proceed to Arrange into Organised Folders**: runs ML + DSA pipeline, then locks the vault

**Page 2: Organised Folders Explorer** (🔐 password required)
- Clickable folder cards (with item counts) for each category + *All Folders*
- **Folder search** shows a properties card: hash-code, total size, file-type breakdown
- **Live global file search** across all folders by name, extension or Doc ID
- **Merge Sort** controls: by Filename / Upload Date / File Size, ascending or descending, with execution time shown
- Table columns: Doc ID, Filename, Folder, Size, Type, Upload Date, **Hash-Code**
- Right-click → copy filename / Doc ID / hash-code / view properties
- **🌳 Visualise Folder Tree** window (whole tree or one category)
- Status bar with live HashMap diagnostics (N, capacity, α, collisions, max chain)

### 7.2 Web App: `python app.py` → http://127.0.0.1:5000 (Flask + HTML/CSS/JS)
The same features with a glassmorphism UI, drag-and-drop upload, a search-scope toggle (all folders / active folder), toast notifications, an animated SHA-256 vault terminal, and a tree visualizer modal.

**REST API** ([web_app.py](web_app.py)):

| Method | Endpoint | Backed by |
| :--- | :--- | :--- |
| GET | `/api/unorganized` | `scan_unorganized_folder` |
| POST | `/api/upload_to_unorganized` | saves uploads to the inbox |
| POST | `/api/arrange` | ML → copy → HashMap + Tree; re-locks vault |
| GET | `/api/organized?folder=` | Tree listing + folder hash-code + HashMap stats |
| GET | `/api/sort?category=&sort_by=&reverse=` | **Merge Sort** |
| GET | `/api/search_files?q=&scope=` | global / scoped search |
| GET | `/api/tree?category=` | ASCII tree + nested dict |
| GET/POST | `/api/security/status`, `/verify`, `/lock` | **SHA-256 vault** |
| POST | `/api/open_explorer?target=` | opens folder in OS file manager |

---

## 🧪 8. Testing & Running

[test_dsa.py](test_dsa.py) has **24 tests, all passing**:

| Test class | Tests | Covers |
| :--- | :---: | :--- |
| `TestCustomHashMap` | 6 | insert/retrieve, update, delete, **forced collisions**, **resize + rehash**, dunder methods |
| `TestCustomFolderTree` | 6 | default folders, create/search, insert, **move**, delete, DFS + ASCII display |
| `TestCustomMergeSort` | 7 | name/size/date asc + desc, **stability**, empty & single-element lists |
| `TestDocumentManagerIntegration` | 5 | upload + auto-categorize, move sync, delete sync, sorting, cross-folder search |

```bash
pip install flask scikit-learn joblib     # dependencies
python -m unittest test_dsa.py -v         # run tests  →  Ran 24 tests ... OK
python demo.py                            # CLI walkthrough of every feature
python gui.py                             # desktop app
python app.py                             # web app (opens browser)
```

---

## 🛡️ 9. Edge Cases Handled

1. **Hash collisions**: chained, no data loss (tested with a forced tiny capacity).
2. **Rehashing**: every key survives capacity doubling.
3. **Duplicate key insert**: updates in place; `size` doesn't grow.
4. **Missing keys**: `get_document_by_id('INVALID')` returns `None`; `m['x']` raises `KeyError`.
5. **Empty / single-element sorts**: return immediately (base case).
6. **Cross-structure delete**: removed from both HashMap and Tree.
7. **Files deleted outside the app**: pruned by `sync_with_disk()`.
8. **Sub-folders in the inbox**: classified by folder name and copied as a whole; size = sum of contents.
9. **Empty / meaningless filenames**: fall back to a default category instead of crashing.
10. **Invalid HashMap config**: capacity ≤ 0 or load factor outside (0.1, 1.0] raises `ValueError`.

---

## ⚠️ 10. Known Limitations & Future Work

- **Model / scikit-learn version mismatch:** the bundled `.pkl` was exported with a newer scikit-learn than the one installed (1.3.2). On load, the TF-IDF step reports *"idf vector is not fitted"* and `MLClassifier` **silently falls back to keyword rules** (confidence exactly 85% or 50%). Fix: re-run the notebook's training and export cells in the same Python environment that runs the app. See [README_ML.md §8](README_ML.md).
- **Tree file lookup is $O(N)$:** could be made $O(1)$ by storing a `doc_id → TreeNode` reference in the HashMap.
- **In-memory only:** the HashMap and Tree are rebuilt from disk on start-up rather than persisted.
- **Vault:** the password is unsalted SHA-256 and the default password is in the source code. A production version would use a salted, slow KDF (bcrypt / PBKDF2) and keep the secret out of code.
- **Minor bug:** `DocumentManager.reset()` sets `_doc_counter` instead of `_id_counter`, so doc IDs keep counting up after a re-arrange instead of restarting at `DOC_1001` (harmless, IDs stay unique).
