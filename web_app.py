"""
web_app.py
Flask Web Application for Digital Junk Drawer.
Serves a modern HTML5, CSS3, and JavaScript frontend.

Endpoints:
- GET  /                           : Renders the web GUI dashboard.
- GET  /api/unorganized            : Scans 'sample_unorganized_files' and returns file metadata.
- POST /api/upload_to_unorganized  : Uploads new files into 'sample_unorganized_files'.
- POST /api/arrange                : Uses ML to classify and arrange files into 'organized_files_output'.
- GET  /api/organized              : Returns folder list, active folder properties, hash-code, and files.
- GET  /api/sort                   : Executes custom recursive Merge Sort across multiple keys and directions.
- POST /api/open_explorer          : Opens folder in native OS Explorer.
"""

import os
import sys
import webbrowser
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from document_manager import DocumentManager
from security_manager import vault_manager

app = Flask(__name__, template_folder="templates")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize central DocumentManager
manager = DocumentManager()

UNORGANIZED_DIR = os.path.abspath("sample_unorganized_files")
ORGANIZED_DIR = os.path.abspath("organized_files_output")

os.makedirs(UNORGANIZED_DIR, exist_ok=True)
os.makedirs(ORGANIZED_DIR, exist_ok=True)

# Initial synchronization with physical disk
manager.sync_with_disk(ORGANIZED_DIR, auto_discover=True)


def get_doc_payload(doc):
    """Formats document with its Custom HashMap Hash-Code."""
    d_dict = doc.to_dict()
    d_dict["hash_code"] = manager.get_doc_hash_code(doc.doc_id)
    return d_dict


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/unorganized", methods=["GET"])
def get_unorganized():
    items = manager.scan_unorganized_folder(UNORGANIZED_DIR)
    return jsonify(items)


@app.route("/api/upload_to_unorganized", methods=["POST"])
def upload_unorganized():
    files = request.files.getlist("files")
    uploaded_count = 0
    for file in files:
        if file.filename:
            save_path = os.path.join(UNORGANIZED_DIR, file.filename)
            file.save(save_path)
            uploaded_count += 1
    return jsonify({"success": True, "uploaded": uploaded_count})


@app.route("/api/arrange", methods=["POST"])
def arrange_files():
    try:
        results = manager.organize_from_unorganized_folder(
            source_dir=UNORGANIZED_DIR,
            target_dir=ORGANIZED_DIR,
            action="copy",
            clean_target=True
        )
        vault_manager.lock()
        return jsonify(results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/api/security/status", methods=["GET"])
def get_security_status():
    return jsonify(vault_manager.get_status())


@app.route("/api/security/verify", methods=["POST"])
def verify_vault_password():
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    res = vault_manager.verify_password(password)
    return jsonify(res)


@app.route("/api/security/lock", methods=["POST"])
def lock_vault_api():
    vault_manager.lock()
    return jsonify({"success": True, "status": "LOCKED", "message": "Organized folders vault locked."})


@app.route("/api/organized", methods=["GET"])
def get_organized():
    folder_param = request.args.get("folder", "All Folders").strip()
    
    # Always synchronize in-memory structures with physical files on disk
    manager.sync_with_disk(ORGANIZED_DIR, auto_discover=True)

    categories = manager.tree.get_categories()
    cat_counts = []
    
    total_docs = manager.list_all_documents(sync_disk=False)
    cat_counts.append({
        "name": "All Folders",
        "count": len(total_docs)
    })
    
    for c in categories:
        docs_in_c = manager.list_documents_in_category(c, sync_disk=False)
        cat_counts.append({
            "name": c,
            "count": len(docs_in_c)
        })

    # Folder properties
    if folder_param == "All Folders":
        total_bytes = sum(d.file_size for d in total_docs)
        b_val = float(total_bytes)
        f_size = f"{total_bytes} B"
        for u in ["B", "KB", "MB", "GB"]:
            if b_val < 1024.0 or u == "GB":
                f_size = f"{b_val:.1f} {u}" if u != "B" else f"{int(b_val)} B"
                break
            b_val /= 1024.0

        folder_props = {
            "category_name": "All Organised Folders",
            "hash_code": f"ROOT_TREE [Cap {manager.storage.capacity}]",
            "file_count": len(total_docs),
            "total_size_bytes": total_bytes,
            "formatted_size": f_size,
            "type_breakdown": f"{len(total_docs)} items indexed in Custom HashMap",
            "folder_path": ORGANIZED_DIR
        }
        docs_to_return = [get_doc_payload(d) for d in total_docs]
    else:
        props = manager.get_category_properties(folder_param, ORGANIZED_DIR)
        if props:
            folder_props = {
                "category_name": props["category_name"],
                "hash_code": props["hash_code"],
                "file_count": props["file_count"],
                "total_size_bytes": props["total_size_bytes"],
                "formatted_size": props["formatted_size"],
                "type_breakdown": props["type_breakdown"],
                "folder_path": props["folder_path"]
            }
            docs_to_return = [get_doc_payload(d) for d in props["documents"]]
        else:
            folder_props = {
                "category_name": folder_param,
                "hash_code": manager.get_category_hash_code(folder_param),
                "file_count": 0,
                "total_size_bytes": 0,
                "formatted_size": "0 B",
                "type_breakdown": "None",
                "folder_path": os.path.join(ORGANIZED_DIR, folder_param.lower())
            }
            docs_to_return = []

    return jsonify({
        "categories": cat_counts,
        "active_folder": folder_param,
        "folder_properties": folder_props,
        "documents": docs_to_return,
        "diagnostics": manager.storage.get_stats()
    })


@app.route("/api/sort", methods=["GET"])
def sort_documents_api():
    category_param = request.args.get("category", "All Folders").strip()
    sort_by = request.args.get("sort_by", "filename").strip()
    reverse_param = request.args.get("reverse", "false").lower() == "true"

    cat = None if category_param == "All Folders" else category_param

    manager.sync_with_disk(ORGANIZED_DIR)
    sorted_docs = manager.sort_documents(category=cat, sort_by=sort_by, reverse=reverse_param, sync_disk=False)
    return jsonify([get_doc_payload(d) for d in sorted_docs])


@app.route("/api/search_files", methods=["GET"])
def search_files_api():
    query = request.args.get("q", "").strip()
    category_param = request.args.get("category", "All Folders").strip()
    scope = request.args.get("scope", "global").strip().lower()

    # Always ensure in-memory state reflects current files on disk
    manager.sync_with_disk(ORGANIZED_DIR)
    cat = None if (scope == "global" or category_param == "All Folders") else category_param
    matched_docs = manager.search_by_name(query, category=cat, sync_disk=False)

    total_bytes = sum(d.file_size for d in matched_docs)
    b_val = float(total_bytes)
    f_size = f"{total_bytes} B"
    for u in ["B", "KB", "MB", "GB"]:
        if b_val < 1024.0 or u == "GB":
            f_size = f"{b_val:.1f} {u}" if u != "B" else f"{int(b_val)} B"
            break
        b_val /= 1024.0

    categories_found = sorted(list(set(d.category for d in matched_docs)))

    return jsonify({
        "query": query,
        "scope": "global" if cat is None else cat,
        "total_matches": len(matched_docs),
        "total_size_bytes": total_bytes,
        "formatted_size": f_size,
        "categories_found": categories_found,
        "documents": [get_doc_payload(d) for d in matched_docs]
    })


@app.route("/api/tree", methods=["GET"])
def get_tree_api():
    category_param = request.args.get("category", "All Folders").strip()
    manager.sync_with_disk(ORGANIZED_DIR)

    ascii_tree = manager.display_tree(category_name=category_param)
    tree_dict = manager.get_tree_dict(category_name=category_param)
    categories = manager.tree.get_categories()

    cat_title = "Digital Junk Drawer (Full Tree)" if category_param == "All Folders" else f"Folder: {category_param}"

    return jsonify({
        "category": category_param,
        "title": cat_title,
        "ascii_tree": ascii_tree,
        "tree_dict": tree_dict,
        "total_categories": len(categories),
        "total_documents": len(manager.list_all_documents(sync_disk=False))
    })


@app.route("/api/open_explorer", methods=["POST"])
def open_explorer_api():
    target = request.args.get("target", "organized")
    target_path = UNORGANIZED_DIR if target == "unorganized" else ORGANIZED_DIR

    if sys.platform == "win32":
        os.startfile(target_path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target_path])
    else:
        subprocess.Popen(["xdg-open", target_path])

    return jsonify({"success": True, "path": target_path})


def run_web_app(open_browser=True, port=5000):
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{port}")
    print(f"[RUNNING] Digital Junk Drawer Web App running at http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    run_web_app()
