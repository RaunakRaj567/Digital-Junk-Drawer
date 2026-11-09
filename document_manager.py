"""
document_manager.py
Unified DocumentManager orchestrating:
1. Custom HashMap   : O(1) document indexing, retrieval, and updates by doc_id.
2. Custom FolderTree: Hierarchical category folder organization and manual re-classification.
3. Custom MergeSort : Stable recursive sorting by filename, file size, or upload date.
4. ML Classifier    : Automated category prediction from document names.

Provides API-ready methods suitable for college project evaluation and frontend integration.
"""

import os
import time
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from dsa.document import Document
from dsa.hash_map import CustomHashMap
from dsa.folder_tree import FolderTree, TreeNode
from dsa.merge_sort import custom_merge_sort
from ml_classifier import MLClassifier


class DocumentManager:
    """
    Central controller for Digital Junk Drawer.
    
    Coordinates the three custom DSA data structures:
    - self.storage : CustomHashMap (fast document access by doc_id)
    - self.tree    : FolderTree (hierarchical folder representation)
    - custom_merge_sort : Sorting algorithm for document listings
    - self.ml      : MLClassifier (auto-categorization engine)
    """

    def __init__(self, model_path: Optional[str] = None):
        self.storage: CustomHashMap = CustomHashMap(capacity=16, load_factor_threshold=0.75)
        self.tree: FolderTree = FolderTree(root_name="Digital Junk Drawer")
        self.ml: MLClassifier = MLClassifier(model_path=model_path)
        self._id_counter: int = 1000

    def _generate_doc_id(self) -> str:
        """Generates a sequential unique document identifier."""
        self._id_counter += 1
        return f"DOC_{self._id_counter}"

    def upload_document(
        self,
        filename: str,
        file_path: str = "",
        file_size: int = 0,
        manual_category: Optional[str] = None,
        custom_id: Optional[str] = None
    ) -> Document:
        """
        Processes a newly uploaded document through the complete DSA + ML pipeline:
        1. Generates unique doc_id if not supplied.
        2. Inspects physical file on disk (if path given) for size and type.
        3. Predicts category via ML model (unless manual_category is specified).
        4. Instantiates Document entity.
        5. Inserts Document into Custom HashMap (O(1) storage).
        6. Inserts Document into Custom Folder Tree under predicted category.
        
        Returns:
        --------
        Document : The created and organized document object.
        """
        doc_id = str(custom_id) if custom_id else self._generate_doc_id()
        
        # Determine actual file size if physical file exists
        actual_size = file_size
        if file_path and os.path.isfile(file_path):
            try:
                actual_size = os.path.getsize(file_path)
            except OSError:
                pass

        # Step 2: Predict Category via Machine Learning (or accept manual override)
        if manual_category:
            assigned_category = str(manual_category).capitalize()
        else:
            predicted_cat, _ = self.ml.predict(filename)
            assigned_category = predicted_cat

        # Step 4: Create Document Entity
        doc = Document(
            doc_id=doc_id,
            filename=filename,
            file_path=file_path if file_path else filename,
            file_size=actual_size,
            upload_timestamp=time.time(),
            category=assigned_category
        )

        # Step 5: Insert into Custom HashMap (keyed by doc_id)
        self.storage.insert(doc.doc_id, doc)

        # Step 6: Insert into Custom Folder Tree
        self.tree.insert_document(assigned_category, doc)

        return doc

    def get_document_by_id(self, doc_id: str) -> Optional[Document]:
        """
        Fast O(1) retrieval of a document by its document ID via Custom HashMap.
        """
        return self.storage.retrieve(str(doc_id))

    def move_document_category(self, doc_id: str, new_category: str) -> bool:
        """
        Manually re-classifies a document and moves it to a new category:
        1. Retrieves document from HashMap.
        2. Moves node in FolderTree from old category to new category.
        3. Synchronously updates category in Document object.
        """
        doc = self.get_document_by_id(doc_id)
        if doc is None:
            return False

        new_cat_title = new_category.strip().capitalize()
        moved = self.tree.move_document(doc_id, new_cat_title)
        if moved:
            doc.category = new_cat_title
            # Update record in HashMap
            self.storage.update(doc_id, doc)
            return True
        return False

    def delete_document(self, doc_id: str) -> bool:
        """
        Deletes a document from both the Custom HashMap and the Custom Folder Tree.
        """
        doc_id_str = str(doc_id)
        doc = self.get_document_by_id(doc_id_str)
        if doc is None:
            return False

        # Remove from Folder Tree
        tree_deleted = self.tree.delete_document(doc_id_str)
        # Remove from Custom HashMap
        map_deleted = self.storage.delete(doc_id_str)

        return tree_deleted and map_deleted

    def reset(self) -> None:
        """
        Resets in-memory Custom HashMap and FolderTree to a clean, empty state.
        """
        self.storage = CustomHashMap(capacity=16, load_factor_threshold=0.75)
        self.tree = FolderTree()
        self._doc_counter = 1000

    def sync_with_disk(
        self,
        organized_dir: str = "organized_files_output",
        auto_discover: bool = False
    ) -> int:
        """
        Synchronizes the in-memory Custom HashMap and FolderTree with actual files on disk.
        
        1. Pruning: Any document whose file was placed in organized_dir but no longer
           exists on disk (e.g. deleted by the user) is immediately removed from both
           the Custom HashMap and the Custom FolderTree.
        2. Auto-Discovery: If auto_discover is True, physical files residing in
           organized_dir/<category>/ that are not yet registered in memory are indexed.
           
        Returns:
        --------
        int : Total active documents remaining in memory after synchronization.
        """
        norm_org = os.path.normpath(os.path.abspath(organized_dir))
        target_path = Path(norm_org)

        # 1. Prune missing documents from memory
        docs_to_delete = []
        for doc in self.storage.values():
            if doc.file_path:
                norm_doc_path = os.path.normpath(os.path.abspath(doc.file_path))
                # If this document is tracked under the organized directory
                if norm_doc_path.startswith(norm_org):
                    if not os.path.exists(doc.file_path):
                        docs_to_delete.append(doc.doc_id)

        for d_id in docs_to_delete:
            self.delete_document(d_id)

        # 2. Discover files present on disk but not yet in memory (if auto_discover is True)
        if auto_discover and target_path.exists():
            existing_paths = {
                os.path.normpath(os.path.abspath(d.file_path))
                for d in self.storage.values()
                if d.file_path
            }

            categories = self.tree.get_categories()
            for cat in categories:
                cat_dir = target_path / cat.lower()
                if cat_dir.exists() and cat_dir.is_dir():
                    for item in cat_dir.iterdir():
                        if item.name.startswith('.'):
                            continue
                        abs_p = os.path.normpath(os.path.abspath(str(item)))
                        if abs_p not in existing_paths:
                            try:
                                if item.is_dir():
                                    f_size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                                else:
                                    f_size = item.stat().st_size
                            except Exception:
                                f_size = 0

                            self.upload_document(
                                filename=item.name,
                                file_path=str(item),
                                file_size=f_size,
                                manual_category=cat
                            )
                            existing_paths.add(abs_p)

        return len(self.storage)

    def list_all_documents(self, sync_disk: bool = True) -> List[Document]:
        """
        Returns a list of all documents stored in the system.
        If sync_disk is True, purges any deleted disk files first.
        """
        if sync_disk:
            self.sync_with_disk()
        return self.storage.values()

    def list_documents_in_category(self, category_name: str, sync_disk: bool = True) -> List[Document]:
        """
        Returns all documents contained within a specific category folder in the tree.
        If sync_disk is True, purges any deleted disk files first.
        """
        if sync_disk:
            self.sync_with_disk()
        return self.tree.get_documents_in_category(category_name)

    def sort_documents(
        self,
        category: Optional[str] = None,
        sort_by: str = "filename",
        reverse: bool = False,
        sync_disk: bool = True
    ) -> List[Document]:
        """
        Sorts documents using Custom Recursive Merge Sort.
        Synchronizes with disk to guarantee that deleted files never appear in sorted output.

        Parameters:
        -----------
        category : Optional[str]
            If specified, sorts only documents within that category.
            If None, sorts all documents across the entire Digital Junk Drawer.
        sort_by : str
            Sorting criterion:
            - 'filename'          : Alphabetical order
            - 'file_size'         : File size
            - 'upload_timestamp'  : Upload date and time
        reverse : bool
            - False : Ascending order (A-Z, smallest to largest, oldest to newest)
            - True  : Descending order (Z-A, largest to smallest, newest to oldest)

        Returns:
        --------
        List[Document] : Stably sorted list of Document objects.
        """
        if sync_disk:
            self.sync_with_disk()

        if category:
            docs = self.list_documents_in_category(category, sync_disk=False)
        else:
            docs = self.list_all_documents(sync_disk=False)

        return custom_merge_sort(docs, sort_key=sort_by, reverse=reverse)

    def search_by_name(self, query: str, category: Optional[str] = None, sync_disk: bool = True) -> List[Document]:
        """
        Searches documents containing query string in their filename, doc_id, or file_type (case-insensitive).
        Synchronizes with disk to guarantee that deleted files never appear in search results.
        
        Parameters:
        -----------
        query : str
            The search term to match.
        category : Optional[str]
            If specified and not 'All Folders', searches only within that category.
            If None or 'All Folders', searches across ALL folders (global multi-folder search).

        Returns:
        --------
        List[Document] : All matching documents from any folder.
        """
        if sync_disk:
            self.sync_with_disk()

        target = query.strip().lower()
        if category and category.strip().lower() != "all folders":
            docs_pool = self.list_documents_in_category(category, sync_disk=False)
        else:
            docs_pool = self.list_all_documents(sync_disk=False)

        if not target:
            return docs_pool

        results = []
        for doc in docs_pool:
            if (target in doc.filename.lower() or 
                target in doc.doc_id.lower() or 
                target in doc.file_type.lower()):
                results.append(doc)
        return results

    def get_doc_hash_code(self, doc_id: str) -> str:
        """Returns the formatted hash-code and bucket index computed by CustomHashMap."""
        hash_val = self.storage._hash(str(doc_id))
        return f"0x{hash_val:04X} [Bucket {hash_val}]"

    def get_category_hash_code(self, category_name: str) -> str:
        """Returns the polynomial hash-code for a category folder."""
        hash_val = self.storage._hash(str(category_name).strip().capitalize())
        return f"0x{hash_val:04X} [Bucket {hash_val}]"

    def scan_unorganized_folder(self, folder_path: str = "sample_unorganized_files") -> List[Dict[str, Any]]:
        """
        Scans unorganized directory and returns raw file metadata before organization.
        """
        path_obj = Path(folder_path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            return []

        items = []
        for item in sorted(path_obj.iterdir()):
            if item.name.startswith('.'):
                continue
            is_dir = item.is_dir()
            size = 0
            if is_dir:
                try:
                    size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                except Exception:
                    size = 4096
            else:
                try:
                    size = item.stat().st_size
                except Exception:
                    size = 0

            # Formatted size
            bytes_val = float(size)
            formatted_size = f"{size} B"
            for unit in ["B", "KB", "MB", "GB"]:
                if bytes_val < 1024.0 or unit == "GB":
                    formatted_size = f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
                    break
                bytes_val /= 1024.0

            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item.stat().st_mtime))
            file_type = "Folder" if is_dir else (item.suffix.lstrip('.').lower() or "file")

            items.append({
                "name": item.name,
                "path": str(item),
                "is_dir": is_dir,
                "size": size,
                "formatted_size": formatted_size,
                "file_type": file_type.upper(),
                "modified_time": mtime
            })
        return items

    def organize_from_unorganized_folder(
        self,
        source_dir: str = "sample_unorganized_files",
        target_dir: str = "organized_files_output",
        action: str = "copy",
        clean_target: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Reads files from sample_unorganized_files, predicts categories via ML,
        copies/moves to organized_files_output/<category>, indexes in CustomHashMap,
        and links into Custom FolderTree.
        
        If clean_target is True (default):
        - Resets the in-memory Custom HashMap and FolderTree to purge all old files.
        - Empties any previously organized files in target_dir subfolders.
        """
        import shutil

        source_path = Path(source_dir)
        target_path = Path(target_dir)

        if not source_path.exists():
            source_path.mkdir(parents=True, exist_ok=True)
            return []

        target_path.mkdir(parents=True, exist_ok=True)

        if clean_target:
            self.reset()
            # Clean old files from organized category folders
            for cat in self.tree.get_categories():
                cat_dir = target_path / cat.lower()
                if cat_dir.exists() and cat_dir.is_dir():
                    for old_file in list(cat_dir.iterdir()):
                        try:
                            if old_file.is_dir():
                                shutil.rmtree(str(old_file))
                            else:
                                old_file.unlink()
                        except Exception:
                            pass

        results = []
        for item in sorted(source_path.iterdir()):
            if item.name.startswith('.'):
                continue

            # Predict category using ML
            predicted_category, confidence = self.ml.predict(item.name)
            cat_folder_name = predicted_category.lower()
            dest_cat_dir = target_path / cat_folder_name
            dest_cat_dir.mkdir(parents=True, exist_ok=True)

            dest_item_path = dest_cat_dir / item.name

            # Size calculation
            if item.is_dir():
                size = sum(f.stat().st_size for f in item.glob('**/*') if f.is_file())
                if action == "move":
                    shutil.move(str(item), str(dest_item_path))
                else:
                    shutil.copytree(str(item), str(dest_item_path), dirs_exist_ok=True)
            else:
                size = item.stat().st_size
                if action == "move":
                    shutil.move(str(item), str(dest_item_path))
                else:
                    shutil.copy2(str(item), str(dest_item_path))

            # Register in DocumentManager (HashMap + Tree)
            doc = self.upload_document(
                filename=item.name,
                file_path=str(dest_item_path),
                file_size=size,
                manual_category=predicted_category
            )

            results.append({
                "doc_id": doc.doc_id,
                "filename": doc.filename,
                "category": doc.category,
                "confidence": confidence,
                "formatted_size": doc.formatted_size,
                "hash_code": self.get_doc_hash_code(doc.doc_id),
                "destination": str(dest_item_path)
            })

        return results

    def get_category_properties(
        self,
        category_name: str,
        target_dir: str = "organized_files_output"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates and returns full properties, statistics, and hash-code for a folder/category.
        """
        cat_title = category_name.strip().capitalize()
        cat_node = self.tree.search_category(cat_title)
        if cat_node is None:
            # Check lower-case match
            for c in self.tree.get_categories():
                if c.lower() == category_name.strip().lower():
                    cat_title = c
                    cat_node = self.tree.search_category(c)
                    break

        if cat_node is None:
            return None

        docs = self.list_documents_in_category(cat_title)
        total_size = sum(d.file_size for d in docs)

        # Formatted size
        bytes_val = float(total_size)
        formatted_size = f"{total_size} B"
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0 or unit == "GB":
                formatted_size = f"{bytes_val:.1f} {unit}" if unit != "B" else f"{int(bytes_val)} B"
                break
            bytes_val /= 1024.0

        # Type counts
        type_counts = {}
        for d in docs:
            t = d.file_type.upper()
            type_counts[t] = type_counts.get(t, 0) + 1

        types_str = ", ".join([f"{ext} ({cnt})" for ext, cnt in type_counts.items()]) if type_counts else "Empty"

        disk_path = os.path.abspath(os.path.join(target_dir, cat_title.lower()))

        return {
            "category_name": cat_title,
            "hash_code": self.get_category_hash_code(cat_title),
            "file_count": len(docs),
            "total_size_bytes": total_size,
            "formatted_size": formatted_size,
            "type_breakdown": types_str,
            "folder_path": disk_path,
            "documents": docs
        }

    def display_tree(self, category_name: Optional[str] = None) -> str:
        """
        Returns visual ASCII representation of the Folder Tree.
        If category_name is specified, returns the subtree for that category.
        """
        return self.tree.display_hierarchy(category_name=category_name)

    def get_tree_dict(self, category_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns nested dictionary representation of the Folder Tree for graphical visual rendering.
        """
        return self.tree.get_tree_dict(category_name=category_name)

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Returns full diagnostic metrics of the DSA structures for evaluation.
        """
        map_stats = self.storage.get_stats()
        categories = self.tree.get_categories()
        cat_counts = {
            cat: len(self.tree.get_documents_in_category(cat))
            for cat in categories
        }

        return {
            "total_documents": len(self.storage),
            "categories_count": len(categories),
            "categories": cat_counts,
            "hash_map_diagnostics": map_stats,
            "ml_model_loaded": self.ml.is_loaded,
            "ml_model_path": self.ml.model_path
        }
