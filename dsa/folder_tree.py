"""
dsa/folder_tree.py
Custom N-ary Tree implementation for hierarchical folder and document organization.

Tree Structure:
Digital Junk Drawer (Root)
├── Business
├── Tech
├── Politics
├── Sports
└── Entertainment
    └── [Document Nodes]
"""

from typing import List, Optional, Dict, Any, Generator, Callable
from .document import Document


class TreeNode:
    """
    Represents a node in the Folder Tree.

    Node Types:
    -----------
    - 'root'     : The topmost root directory ("Digital Junk Drawer")
    - 'category' : A major category folder (e.g. "Business", "Sports", "Tech")
    - 'document' : A leaf node representing a document
    """

    def __init__(
        self,
        name: str,
        node_type: str = "category",
        document: Optional[Document] = None,
        parent: Optional['TreeNode'] = None
    ):
        self.name: str = str(name).strip()
        self.node_type: str = str(node_type).lower()  # 'root', 'category', 'document'
        self.document: Optional[Document] = document
        self.parent: Optional['TreeNode'] = parent
        self.children: List['TreeNode'] = []

    def is_root(self) -> bool:
        return self.node_type == "root"

    def is_category(self) -> bool:
        return self.node_type == "category"

    def is_document(self) -> bool:
        return self.node_type == "document"

    def add_child(self, child_node: 'TreeNode') -> None:
        """Adds a child node and links parent pointer."""
        child_node.parent = self
        self.children.append(child_node)

    def remove_child(self, child_node: 'TreeNode') -> bool:
        """Removes a direct child node."""
        if child_node in self.children:
            self.children.remove(child_node)
            child_node.parent = None
            return True
        return False

    def find_child_by_name(self, name: str) -> Optional['TreeNode']:
        """Searches direct children by name (case-insensitive)."""
        target = name.strip().lower()
        for child in self.children:
            if child.name.lower() == target:
                return child
        return None

    def __repr__(self) -> str:
        return f"TreeNode(name={self.name!r}, type={self.node_type!r}, children={len(self.children)})"


class FolderTree:
    """
    Hierarchical Folder Tree for Digital Junk Drawer.

    Features:
    - Root node: "Digital Junk Drawer"
    - Default categories: Business, Tech, Politics, Sports, Entertainment
    - Dynamic creation of custom categories
    - Insertion of document leaf nodes into designated categories
    - Search for categories and documents
    - Moving documents between categories (manual re-classification)
    - Deletion of document nodes
    - Depth-First Search (DFS) traversal
    - Visual ASCII hierarchy display
    """

    DEFAULT_CATEGORIES = [
        "Business",
        "Tech",
        "Politics",
        "Sports",
        "Entertainment"
    ]

    def __init__(self, root_name: str = "Digital Junk Drawer"):
        self.root: TreeNode = TreeNode(name=root_name, node_type="root")
        
        # Initialize default major categories
        for cat in self.DEFAULT_CATEGORIES:
            self.create_category(cat)

    def create_category(self, category_name: str) -> TreeNode:
        """
        Creates a new category folder under the root if it does not already exist.
        Returns the category TreeNode.
        """
        category_name = category_name.strip()
        existing = self.search_category(category_name)
        if existing is not None:
            return existing

        new_category = TreeNode(name=category_name, node_type="category", parent=self.root)
        self.root.add_child(new_category)
        return new_category

    def search_category(self, category_name: str) -> Optional[TreeNode]:
        """
        Searches for a category node under the root (case-insensitive).
        Returns the category TreeNode if found, else None.
        """
        target = category_name.strip().lower()
        for child in self.root.children:
            if child.is_category() and child.name.lower() == target:
                return child
        return None

    def get_categories(self) -> List[str]:
        """Returns a list of all category names in the tree."""
        return [c.name for c in self.root.children if c.is_category()]

    def insert_document(self, category_name: str, document: Document) -> TreeNode:
        """
        Inserts a document node into the specified category.
        If category does not exist, it is created automatically.
        Updates the document's category attribute to match the target category.
        """
        category_node = self.search_category(category_name)
        if category_node is None:
            category_node = self.create_category(category_name)

        # Update document's internal category record
        document.category = category_node.name

        doc_node = TreeNode(
            name=document.filename,
            node_type="document",
            document=document,
            parent=category_node
        )
        category_node.add_child(doc_node)
        return doc_node

    def search_document_node(self, doc_id: str) -> Optional[TreeNode]:
        """
        Searches for a document node anywhere in the tree by its unique doc_id.
        Uses Depth-First Search.
        """
        for node in self.dfs():
            if node.is_document() and node.document is not None:
                if str(node.document.doc_id) == str(doc_id):
                    return node
        return None

    def delete_document(self, doc_id: str) -> bool:
        """
        Deletes a document node matching doc_id from its containing category.
        Returns True if deleted, False if document was not found.
        """
        doc_node = self.search_document_node(doc_id)
        if doc_node is not None and doc_node.parent is not None:
            return doc_node.parent.remove_child(doc_node)
        return False

    def move_document(self, doc_id: str, target_category_name: str) -> bool:
        """
        Moves a document from its current category to target_category_name.
        1. Finds existing document node in tree.
        2. Removes it from current category parent.
        3. Appends it to target category parent (created if not exists).
        4. Synchronously updates document.category metadata.
        Returns True if successfully moved, False if document not found.
        """
        doc_node = self.search_document_node(doc_id)
        if doc_node is None:
            return False

        target_category = self.search_category(target_category_name)
        if target_category is None:
            target_category = self.create_category(target_category_name)

        # Remove from old parent
        if doc_node.parent is not None:
            doc_node.parent.remove_child(doc_node)

        # Add to new parent
        target_category.add_child(doc_node)

        # Update document category property
        if doc_node.document is not None:
            doc_node.document.category = target_category.name

        return True

    def get_documents_in_category(self, category_name: str) -> List[Document]:
        """Returns all documents contained within a specific category folder."""
        cat_node = self.search_category(category_name)
        if cat_node is None:
            return []
        
        docs = []
        for child in cat_node.children:
            if child.is_document() and child.document is not None:
                docs.append(child.document)
        return docs

    def get_all_documents(self) -> List[Document]:
        """Collects all Document objects across all categories in the tree."""
        all_docs = []
        for node in self.dfs():
            if node.is_document() and node.document is not None:
                all_docs.append(node.document)
        return all_docs

    def dfs(self, start_node: Optional[TreeNode] = None) -> Generator[TreeNode, None, None]:
        """
        Performs Depth-First Search (DFS) pre-order traversal starting from start_node.
        Yields each TreeNode encountered.
        """
        if start_node is None:
            start_node = self.root

        yield start_node
        for child in start_node.children:
            yield from self.dfs(child)

    def display_hierarchy(self, category_name: Optional[str] = None) -> str:
        """
        Generates and returns an ASCII visual representation of the folder tree.
        If category_name is provided (and not 'All Folders'), visualizes the subtree
        for that specific category folder. Otherwise, visualizes the entire tree from the root.
        """
        lines = []

        start_node = self.root
        if category_name and category_name.strip().lower() != "all folders":
            found = self.search_category(category_name)
            if found:
                start_node = found
            else:
                return f"Category '{category_name}' not found in FolderTree."

        def _build_tree(node: TreeNode, prefix: str = "", is_last: bool = True, is_top: bool = True):
            if is_top:
                if node.is_root():
                    lines.append(f"📦 {node.name}/ [Root Node | Total Categories: {len(node.children)}]")
                elif node.is_category():
                    doc_count = len([c for c in node.children if c.is_document()])
                    parent_name = node.parent.name if node.parent else "None"
                    lines.append(f"📂 {node.name}/ [Category Node | Parent: {parent_name} | Items: {doc_count}]")
            else:
                marker = "└── " if is_last else "├── "
                if node.is_category():
                    doc_count = len([c for c in node.children if c.is_document()])
                    lines.append(f"{prefix}{marker}📂 {node.name}/ ({doc_count} items)")
                elif node.is_document() and node.document is not None:
                    lines.append(
                        f"{prefix}{marker}📄 [{node.document.doc_id}] {node.name} "
                        f"({node.document.file_type.upper()}, {node.document.formatted_size})"
                    )

            # Child prefix indentation
            child_prefix = prefix
            if not is_top:
                child_prefix += "    " if is_last else "│   "

            for i, child in enumerate(node.children):
                last_child = (i == len(node.children) - 1)
                _build_tree(child, child_prefix, last_child, is_top=False)

        _build_tree(start_node)
        return "\n".join(lines)

    def get_tree_dict(self, category_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Exports the tree (or a specific category subtree) as a nested dictionary
        for graphical visual tree rendering in Web and GUI components.
        """
        start_node = self.root
        if category_name and category_name.strip().lower() != "all folders":
            found = self.search_category(category_name)
            if found:
                start_node = found

        def _node_to_dict(node: TreeNode) -> Dict[str, Any]:
            data = {
                "name": node.name,
                "node_type": node.node_type,
                "parent": node.parent.name if node.parent else None,
                "children": [_node_to_dict(c) for c in node.children]
            }
            if node.is_document() and node.document is not None:
                data["doc_id"] = node.document.doc_id
                data["file_type"] = node.document.file_type.upper()
                data["formatted_size"] = node.document.formatted_size
                data["upload_time"] = node.document.formatted_timestamp
                data["category"] = node.document.category
            elif node.is_category():
                data["doc_count"] = len([c for c in node.children if c.is_document()])
            elif node.is_root():
                data["category_count"] = len(node.children)
            return data

        return _node_to_dict(start_node)
