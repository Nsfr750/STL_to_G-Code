"""
Markdown Viewer for STL to GCode Converter
"""
import os
import markdown
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, 
    QHBoxLayout, QFileDialog, QListWidget, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QUrl

class MarkdownViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Documentation Viewer")
        self.setMinimumSize(900, 700)
        
        # Get docs directory
        self.docs_dir = os.path.abspath(os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'docs'
        ))
        
        self.setup_ui()
        self.load_documents()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setMinimumWidth(250)
        self.file_list.itemClicked.connect(self.on_file_selected)
        
        # Content viewer
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.setOpenLinks(False)
        self.text_browser.anchorClicked.connect(self.on_anchor_clicked)
        self.apply_styles()
        
        splitter.addWidget(self.file_list)
        splitter.addWidget(self.text_browser)
        splitter.setSizes([250, 650])
        layout.addWidget(splitter)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def load_documents(self):
        if not os.path.exists(self.docs_dir):
            os.makedirs(self.docs_dir, exist_ok=True)
            return
            
        self.file_list.clear()
        for root, _, files in os.walk(self.docs_dir):
            for file in sorted(files):
                if file.lower().endswith('.md'):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), 
                        self.docs_dir
                    )
                    self.file_list.addItem(rel_path)
    
    def on_file_selected(self, item):
        file_path = os.path.join(self.docs_dir, item.text())
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Configure markdown extensions
            extensions = [
                'markdown.extensions.extra',
                'markdown.extensions.toc',
                'markdown.extensions.tables',
                'markdown.extensions.fenced_code',
                'markdown.extensions.codehilite',
                'markdown.extensions.nl2br',
                'markdown.extensions.sane_lists',
                'markdown.extensions.smarty',
                'pymdownx.extra',
                'pymdownx.highlight',
                'pymdownx.superfences',
                'markdown.extensions.md_in_html',  # For raw HTML in markdown
                'pymdownx.emoji',
                'pymdownx.tabbed',
                'pymdownx.tasklist',
                'pymdownx.superfences',
                'pymdownx.details',
                'pymdownx.inlinehilite',
                'pymdownx.magiclink'
            ]
            
            # Process markdown
            html = markdown.markdown(
                content,
                extensions=extensions,
                output_format='html5',
                extension_configs={
                    'markdown.extensions.toc': {
                        'toc_depth': '2-4',
                        'permalink': ' ',  # Add permalinks
                        'baselevel': 2
                    },
                    'markdown.extensions.codehilite': {
                        'use_pygments': True,
                        'noclasses': True,
                        'pygments_style': 'monokai',
                    },
                    'pymdownx.highlight': {
                        'use_pygments': True,
                        'noclasses': True,
                        'pygments_style': 'monokai',
                    }
                }
            )
            
            # Get the base directory of the current file
            file_dir = os.path.dirname(file_path)
            
            # Add CSS styles
            css_style = """
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #e0e0e0;
                background-color: #2b2b2b;
                padding: 20px;
                max-width: 900px;
                margin: 0 auto;
            }
            a { color: #4da6ff; text-decoration: none; }
            a:hover { text-decoration: underline; }
            img { 
                max-width: 100%; 
                height: auto;
                display: block;
                margin: 1em auto;
                border: 1px solid #444;
                border-radius: 4px;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #e0e0e0;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                border-bottom: 1px solid #444;
                padding-bottom: 0.3em;
            }
            pre, code {
                background-color: #1e1e1e;
                font-family: 'Consolas', 'Monaco', monospace;
                border-radius: 4px;
            }
            pre {
                padding: 12px;
                overflow-x: auto;
                border: 1px solid #444;
            }
            code { padding: 2px 4px; }
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
                color: #fff;
            }
            tr:nth-child(even) { background-color: #2d2d2d; }
            blockquote {
                border-left: 4px solid #555;
                margin: 1em 0;
                padding: 0.5em 1em;
                color: #aaa;
                background-color: #2d2d2d;
            }
            /* TOC specific styles */
            .toc {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 20px;
            }
            .toc-title {
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 1.2em;
            }
            .toc ul, .toc ol {
                padding-left: 20px;
                margin: 5px 0;
            }
            .toc a::after {
                content: '#';
                color: #666;
                margin-left: 5px;
                text-decoration: none;
            }
            """
            
            # Create the HTML document with embedded CSS and proper base URL
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <base href="{QUrl.fromLocalFile(file_dir + os.sep).toString()}">
                <style>{css_style}</style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
            
            self.text_browser.setHtml(styled_html)
            self.text_browser.document().setBaseUrl(
                QUrl.fromLocalFile(os.path.dirname(file_path) + os.sep)
            )
            
        except Exception as e:
            self.text_browser.setHtml(f"<p style='color:red'>Error loading file: {str(e)}</p>")
    
    def on_anchor_clicked(self, url):
        if url.isLocalFile() and url.toLocalFile().lower().endswith('.md'):
            # Find and select the file in the list
            rel_path = os.path.relpath(url.toLocalFile(), self.docs_dir)
            items = self.file_list.findItems(rel_path, Qt.MatchFlag.MatchExactly)
            if items:
                self.file_list.setCurrentItem(items[0])
                self.on_file_selected(items[0])
        else:
            # Open external links in default browser
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)
    
    def apply_styles(self):
        # Additional styles can be applied here if needed
        pass

def show_documentation(parent=None):
    viewer = MarkdownViewer(parent)
    if viewer.file_list.count() > 0:
        viewer.exec()
    else:
        QMessageBox.information(
            parent,
            "No Documentation",
            "No markdown files found in the docs directory."
        )
