"""
app.py
Main entry point for running the Digital Junk Drawer Web Application (HTML/CSS/JS).
Run with:
    python app.py
"""

from web_app import run_web_app

if __name__ == "__main__":
    run_web_app(open_browser=True, port=5000)
