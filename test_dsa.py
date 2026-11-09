"""
test_dsa.py
Comprehensive unit test suite for all custom DSA components and DocumentManager.
Covers:
1. Custom HashMap (insertion, collisions, updates, deletion, resizing, edge cases).
2. Custom FolderTree (creation, insertion, category move, deletion, DFS, hierarchy).
3. Custom MergeSort (filename, size, timestamp sorting, asc/desc, stability, edge cases).
4. DocumentManager Integration (end-to-end workflow, sync between HashMap and Tree).
"""

import unittest
import time
import warnings

# Suppress sklearn unpickle warnings during testing
warnings.simplefilter("ignore")
from dsa.document import Document
from dsa.hash_map import CustomHashMap, HashNode
from dsa.folder_tree import FolderTree, TreeNode
from dsa.merge_sort import custom_merge_sort
from document_manager import DocumentManager


class TestCustomHashMap(unittest.TestCase):
    """Unit tests for the Custom HashMap."""

    def setUp(self):
        self.map = CustomHashMap(capacity=4, load_factor_threshold=0.75)

    def test_insert_and_retrieve(self):
        self.map.insert("DOC_1", "Document One")
        self.map.insert("DOC_2", "Document Two")
        self.assertEqual(self.map.retrieve("DOC_1"), "Document One")
        self.assertEqual(self.map.retrieve("DOC_2"), "Document Two")
        self.assertIsNone(self.map.retrieve("DOC_NON_EXISTENT"))

    def test_update_existing_key(self):
        self.map.insert("DOC_1", "Initial Content")
        self.assertEqual(self.map.retrieve("DOC_1"), "Initial Content")
        self.assertEqual(len(self.map), 1)

        # Update via insert
        self.map.insert("DOC_1", "Updated Content")
        self.assertEqual(self.map.retrieve("DOC_1"), "Updated Content")
        self.assertEqual(len(self.map), 1)

        # Update via update method
        success = self.map.update("DOC_1", "Second Update")
        self.assertTrue(success)
        self.assertEqual(self.map.retrieve("DOC_1"), "Second Update")

        # Update non-existent key
        fail = self.map.update("DOC_999", "No Entry")
        self.assertFalse(fail)

    def test_delete(self):
        self.map.insert("K1", "V1")
        self.map.insert("K2", "V2")
        self.map.insert("K3", "V3")

        self.assertEqual(len(self.map), 3)
        self.assertTrue(self.map.delete("K2"))
        self.assertIsNone(self.map.retrieve("K2"))
        self.assertEqual(len(self.map), 2)

        # Delete non-existent
        self.assertFalse(self.map.delete("K2"))

    def test_collision_handling(self):
        """Force collisions into the same bucket to test separate chaining."""
        # Create a small map with capacity 1 to force every key into bucket 0
        small_map = CustomHashMap(capacity=1, load_factor_threshold=1.0)
        # Manually disable resizing for this specific test
        small_map.load_factor_threshold = 100.0

        small_map.insert("A", "Alpha")
        small_map.insert("B", "Beta")
        small_map.insert("C", "Gamma")

        self.assertEqual(small_map.retrieve("A"), "Alpha")
        self.assertEqual(small_map.retrieve("B"), "Beta")
        self.assertEqual(small_map.retrieve("C"), "Gamma")

        # Verify chain deletion from middle
        self.assertTrue(small_map.delete("B"))
        self.assertIsNone(small_map.retrieve("B"))
        self.assertEqual(small_map.retrieve("A"), "Alpha")
        self.assertEqual(small_map.retrieve("C"), "Gamma")

    def test_dynamic_resizing_and_rehashing(self):
        """Verify capacity doubles and elements are preserved when threshold is crossed."""
        initial_cap = self.map.capacity
        self.assertEqual(initial_cap, 4)

        # Inserting 4 elements will cross threshold (3 / 4 = 0.75)
        self.map.insert("K1", "V1")
        self.map.insert("K2", "V2")
        self.map.insert("K3", "V3")
        self.map.insert("K4", "V4")

        self.assertGreater(self.map.capacity, initial_cap)
        self.assertEqual(self.map.capacity, 8)
        # Verify all elements survived rehashing
        self.assertEqual(self.map.retrieve("K1"), "V1")
        self.assertEqual(self.map.retrieve("K2"), "V2")
        self.assertEqual(self.map.retrieve("K3"), "V3")
        self.assertEqual(self.map.retrieve("K4"), "V4")

    def test_keys_values_items_and_dunder_methods(self):
        self.map["ID_1"] = 100
        self.map["ID_2"] = 200
        self.assertTrue("ID_1" in self.map)
        self.assertEqual(self.map["ID_1"], 100)
        self.assertEqual(sorted(self.map.keys()), ["ID_1", "ID_2"])
        self.assertEqual(sorted(self.map.values()), [100, 200])
        del self.map["ID_1"]
        self.assertFalse("ID_1" in self.map)


class TestCustomFolderTree(unittest.TestCase):
    """Unit tests for the Custom Folder Tree."""

    def setUp(self):
        self.tree = FolderTree(root_name="Digital Junk Drawer")
        self.doc1 = Document(doc_id="D1", filename="annual_tax_filing.pdf", category="Business")
        self.doc2 = Document(doc_id="D2", filename="premier_league_goals.mp4", category="Sports")

    def test_default_categories_initialization(self):
        cats = self.tree.get_categories()
        expected = ["Business", "Tech", "Politics", "Sports", "Entertainment"]
        for cat in expected:
            self.assertIn(cat, cats)

    def test_create_and_search_category(self):
        node = self.tree.create_category("Research")
        self.assertIsNotNone(node)
        self.assertEqual(node.name, "Research")

        # Search existing
        found = self.tree.search_category("research")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Research")

        # Search non-existing
        self.assertIsNone(self.tree.search_category("NonExistent"))

    def test_insert_and_get_documents(self):
        self.tree.insert_document("Business", self.doc1)
        self.tree.insert_document("Sports", self.doc2)

        bus_docs = self.tree.get_documents_in_category("Business")
        sport_docs = self.tree.get_documents_in_category("Sports")

        self.assertEqual(len(bus_docs), 1)
        self.assertEqual(bus_docs[0].filename, "annual_tax_filing.pdf")
        self.assertEqual(len(sport_docs), 1)
        self.assertEqual(sport_docs[0].filename, "premier_league_goals.mp4")

    def test_move_document_between_categories(self):
        self.tree.insert_document("Business", self.doc1)
        self.assertEqual(self.doc1.category, "Business")

        # Move to Tech
        success = self.tree.move_document("D1", "Tech")
        self.assertTrue(success)

        # Check old category is empty
        self.assertEqual(len(self.tree.get_documents_in_category("Business")), 0)
        # Check new category has doc
        tech_docs = self.tree.get_documents_in_category("Tech")
        self.assertEqual(len(tech_docs), 1)
        self.assertEqual(tech_docs[0].doc_id, "D1")
        self.assertEqual(self.doc1.category, "Tech")

    def test_delete_document(self):
        self.tree.insert_document("Business", self.doc1)
        self.assertTrue(self.tree.delete_document("D1"))
        self.assertEqual(len(self.tree.get_documents_in_category("Business")), 0)
        # Delete non-existent
        self.assertFalse(self.tree.delete_document("D1"))

    def test_dfs_and_display_hierarchy(self):
        self.tree.insert_document("Business", self.doc1)
        nodes = list(self.tree.dfs())
        node_names = [n.name for n in nodes]
        self.assertIn("Digital Junk Drawer", node_names)
        self.assertIn("Business", node_names)
        self.assertIn("annual_tax_filing.pdf", node_names)

        display_str = self.tree.display_hierarchy()
        self.assertIn("📦 Digital Junk Drawer/", display_str)
        self.assertIn("📂 Business/", display_str)
        self.assertIn("annual_tax_filing.pdf", display_str)


class TestCustomMergeSort(unittest.TestCase):
    """Unit tests for Custom Merge Sort."""

    def setUp(self):
        self.docs = [
            Document("1", "zebra_report.pdf", file_size=500, upload_timestamp=100.0),
            Document("2", "apple_notes.txt", file_size=1500, upload_timestamp=300.0),
            Document("3", "mango_data.csv", file_size=200, upload_timestamp=200.0),
            Document("4", "banana_slides.pptx", file_size=1500, upload_timestamp=150.0)
        ]

    def test_sort_by_filename_ascending(self):
        sorted_docs = custom_merge_sort(self.docs, sort_key="filename", reverse=False)
        names = [d.filename for d in sorted_docs]
        self.assertEqual(names, ["apple_notes.txt", "banana_slides.pptx", "mango_data.csv", "zebra_report.pdf"])

    def test_sort_by_filename_descending(self):
        sorted_docs = custom_merge_sort(self.docs, sort_key="filename", reverse=True)
        names = [d.filename for d in sorted_docs]
        self.assertEqual(names, ["zebra_report.pdf", "mango_data.csv", "banana_slides.pptx", "apple_notes.txt"])

    def test_sort_by_file_size_ascending(self):
        sorted_docs = custom_merge_sort(self.docs, sort_key="file_size", reverse=False)
        sizes = [d.file_size for d in sorted_docs]
        self.assertEqual(sizes, [200, 500, 1500, 1500])

    def test_sort_by_file_size_descending(self):
        sorted_docs = custom_merge_sort(self.docs, sort_key="file_size", reverse=True)
        sizes = [d.file_size for d in sorted_docs]
        self.assertEqual(sizes, [1500, 1500, 500, 200])

    def test_sort_by_upload_date(self):
        sorted_asc = custom_merge_sort(self.docs, sort_key="upload_timestamp", reverse=False)
        times_asc = [d.upload_timestamp for d in sorted_asc]
        self.assertEqual(times_asc, [100.0, 150.0, 200.0, 300.0])

        sorted_desc = custom_merge_sort(self.docs, sort_key="upload_timestamp", reverse=True)
        times_desc = [d.upload_timestamp for d in sorted_desc]
        self.assertEqual(times_desc, [300.0, 200.0, 150.0, 100.0])

    def test_sorting_stability(self):
        """Documents with equal file_size must preserve their initial relative order."""
        docA = Document("A", "doc_A.txt", file_size=1000)
        docB = Document("B", "doc_B.txt", file_size=1000)
        docC = Document("C", "doc_C.txt", file_size=1000)

        initial = [docA, docB, docC]
        sorted_res = custom_merge_sort(initial, sort_key="file_size", reverse=False)
        ids = [d.doc_id for d in sorted_res]
        self.assertEqual(ids, ["A", "B", "C"])

    def test_edge_cases(self):
        # Empty list
        self.assertEqual(custom_merge_sort([], sort_key="filename"), [])
        # Single element
        single = [self.docs[0]]
        self.assertEqual(custom_merge_sort(single, sort_key="filename"), single)


class TestDocumentManagerIntegration(unittest.TestCase):
    """End-to-End integration tests for DocumentManager."""

    def setUp(self):
        self.mgr = DocumentManager()

    def test_upload_and_auto_categorization(self):
        doc1 = self.mgr.upload_document("champions_league_football_final.mp4", file_size=2500000)
        doc2 = self.mgr.upload_document("Tesla_Quarterly_Financial_Report.xlsx", file_size=120000)

        self.assertEqual(doc1.category, "Sports")
        self.assertEqual(doc2.category, "Business")

        # Verify presence in Custom HashMap
        retrieved = self.mgr.get_document_by_id(doc1.doc_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.filename, "champions_league_football_final.mp4")

        # Verify presence in Tree
        sports_docs = self.mgr.list_documents_in_category("Sports")
        self.assertIn(doc1, sports_docs)

    def test_manual_category_move_synchronization(self):
        doc = self.mgr.upload_document("parliament_election_turnout.pdf", file_size=80000)
        self.assertEqual(doc.category, "Politics")

        # Manually move to Business
        success = self.mgr.move_document_category(doc.doc_id, "Business")
        self.assertTrue(success)

        # Check HashMap reflects change
        retrieved = self.mgr.get_document_by_id(doc.doc_id)
        self.assertEqual(retrieved.category, "Business")

        # Check Tree reflects change
        self.assertNotIn(doc, self.mgr.list_documents_in_category("Politics"))
        self.assertIn(doc, self.mgr.list_documents_in_category("Business"))

    def test_delete_synchronization(self):
        doc = self.mgr.upload_document("nvidia_rtx_gpu_ai_benchmark.py", file_size=45000)
        doc_id = doc.doc_id

        self.assertTrue(self.mgr.delete_document(doc_id))
        self.assertIsNone(self.mgr.get_document_by_id(doc_id))
        self.assertNotIn(doc, self.mgr.list_documents_in_category("Tech"))

    def test_integrated_sorting(self):
        self.mgr.upload_document("zebra.txt", file_size=100)
        self.mgr.upload_document("apple.txt", file_size=500)
        self.mgr.upload_document("mango.txt", file_size=300)

        sorted_docs = self.mgr.sort_documents(sort_by="filename", reverse=False)
        names = [d.filename for d in sorted_docs]
        self.assertEqual(names, ["apple.txt", "mango.txt", "zebra.txt"])

    def test_cross_folder_file_search(self):
        """Tests searching for files across all folders by name/substring/type."""
        doc1 = self.mgr.upload_document("quarterly_financial_report.xlsx", file_size=20000)  # Business
        doc2 = self.mgr.upload_document("premier_league_match_report.mp4", file_size=90000)  # Sports
        doc3 = self.mgr.upload_document("tech_ai_breakthrough_report.pdf", file_size=50000)   # Tech

        # Global search for "report" should find documents across Business, Sports, and Tech
        results = self.mgr.search_by_name("report", category=None)
        self.assertEqual(len(results), 3)

        filenames = [d.filename for d in results]
        self.assertIn("quarterly_financial_report.xlsx", filenames)
        self.assertIn("premier_league_match_report.mp4", filenames)
        self.assertIn("tech_ai_breakthrough_report.pdf", filenames)

        # Search by unique substring across any folder
        match_ai = self.mgr.search_by_name("ai_breakthrough")
        self.assertEqual(len(match_ai), 1)
        self.assertEqual(match_ai[0].category, "Tech")

        # Category-scoped search
        scoped_results = self.mgr.search_by_name("report", category="Sports")
        self.assertEqual(len(scoped_results), 1)
        self.assertEqual(scoped_results[0].category, "Sports")
        self.assertEqual(scoped_results[0].filename, "premier_league_match_report.mp4")


if __name__ == "__main__":
    unittest.main()
