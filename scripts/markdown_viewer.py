"""
Markdown Viewer for STL to GCode Converter

This module provides a simple markdown viewer with syntax highlighting.
"""
import os
import markdown
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, QPushButton, 
                            QFileDialog, QHBoxLayout, QLabel, QComboBox, QFrame)
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtGui import QTextDocument, QTextCharFormat, QTextCursor, QTextFormat, QTextBlockFormat, QTextFrameFormat, QTextLength

class MarkdownViewer(QDialog):
    """A simple markdown viewer dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Documentation")
        self.setMinimumSize(800, 600)
        
        # Store the docs directory path
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')
        
        self.setup_ui()
        self.load_documentation_list()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Document selector
        self.doc_selector = QComboBox()
        self.doc_selector.currentTextChanged.connect(self.load_markdown_file)
        toolbar.addWidget(QLabel("Document:"))
        toolbar.addWidget(self.doc_selector, 1)
        
        # Add some stretch
        toolbar.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        toolbar.addWidget(close_btn)
        
        layout.addLayout(toolbar)
        
        # Text browser for rendering markdown
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                font-family: Arial, sans-serif;
            }
            a {
                color: #4da6ff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            pre, code {
                background-color: #1e1e1e;
                font-family: 'Consolas', monospace;
                border-radius: 4px;
            }
            pre {
                padding: 10px;
                margin: 5px 0;
            }
            code {
                padding: 2px 4px;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #e6e6e6;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }
            table {
                border-collapse: collapse;
                margin: 1em 0;
                width: 100%;
                border: 1px solid #444;
            }
            th, td {
                border: 1px solid #444;
                padding: 8px 12px;
                text-align: left;
            }
            th {
                background-color: #333;
            }
            tr:nth-child(even) {
                background-color: #2d2d2d;
            }
            blockquote {
                border-left: 4px solid #555;
                margin: 1em 0;
                padding: 0 1em;
                color: #aaa;
            }
        """)
        
        layout.addWidget(self.text_browser)
    
    def load_documentation_list(self):
        """Load the list of available markdown files."""
        if not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir, exist_ok=True)
            return
            
        # Find all markdown files
        md_files = [f for f in os.listdir(self.docs_dir) 
                   if f.endswith('.md') and os.path.isfile(os.path.join(self.docs_dir, f))]
        
        self.doc_selector.clear()
        for md_file in sorted(md_files):
            self.doc_selector.addItem(md_file)
    
    def load_markdown_file(self, filename):
        """Load and display a markdown file."""
        if not filename:
            return
            
        filepath = os.path.join(self.docs_dir, filename)
        if not os.path.exists(filepath):
            self.text_browser.setHtml(f"<p style='color: red;'>File not found: {filename}</p>")
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert markdown to HTML
            html = markdown.markdown(
                content,
                extensions=[
                    'fenced_code',
                    'codehilite',
                    'tables',
                    'toc'
                ],
                extension_configs={
                    'codehilite': {
                        'use_pygments': True,
                        'noclasses': True,
                        'pygments_style': 'monokai',
                    }
                },
                output_format='html5'
            )
            
            # Set the HTML content
            self.text_browser.setHtml(html)
            
        except Exception as e:
            self.text_browser.setHtml(f"<p style='color: red;'>Error loading {filename}: {str(e)}</p>")


def show_documentation(parent=None):
    """Show the documentation viewer dialog."""
    viewer = MarkdownViewer(parent)
    if viewer.doc_selector.count() > 0:
        viewer.exec()
    else:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            parent, 
            "No Documentation Found",
            "No markdown documentation files (*.md) were found in the 'docs' directory."
        )
