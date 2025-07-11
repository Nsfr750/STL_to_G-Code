"""
UI styling and layout management for STL to GCode Converter using PyQt6.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStatusBar,
    QProgressBar, QListWidget, QFrame, QSizePolicy, QApplication, QCheckBox, QDoubleSpinBox,
    QToolBar, QToolButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPalette, QColor, QFont, QIcon
from PyQt6.Qsci import QsciScintilla, QsciLexerCustom, QsciLexerPython

class UI:
    """UI styling and widget management class for PyQt6."""
    
    def __init__(self, parent=None):
        """Initialize the UI manager with the given parent widget."""
        self.parent = parent
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure application styles using QSS (Qt Style Sheets)."""
        # Define the stylesheet
        stylesheet = """
            QWidget {
                background-color: #2b2b2b;
                color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QPushButton {
                background-color: #424242;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 100px;
                min-height: 32px;
                margin: 2px;
                font-size: 12px;
                font-weight: 500;
                text-align: center;
            }
            
            QPushButton:hover {
                background-color: #555;
                border-color: #777;
            }
            
            QPushButton:pressed {
                background-color: #666;
                border-color: #888;
            }
            
            QPushButton:disabled {
                background-color: #333;
                color: #666;
                border-color: #444;
            }
            
            QPushButton#primaryButton {
                background-color: #1976D2;
                font-weight: bold;
                min-width: 120px;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #1E88E5;
                border-color: #42A5F5;
            }
            
            QPushButton#primaryButton:pressed {
                background-color: #1565C0;
            }
            
            QPushButton#dangerButton {
                background-color: #C62828;
                color: white;
                font-weight: bold;
            }
            
            QPushButton#dangerButton:hover {
                background-color: #D32F2F;
                border-color: #EF5350;
            }
            
            QPushButton#dangerButton:pressed {
                background-color: #B71C1C;
            }
            
            QPushButton#successButton {
                background-color: #2E7D32;
                color: white;
                font-weight: bold;
            }
            
            QPushButton#successButton:hover {
                background-color: #388E3C;
                border-color: #66BB6A;
            }
            
            QPushButton#successButton:pressed {
                background-color: #1B5E20;
            }
            
            QLabel {
                color: #EEEEEE;
            }
            
            QLabel#titleLabel {
                font-size: 16px;
                font-weight: bold;
                color: #64B5F6;
            }
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #1976D2;
            }
            
            QListWidget, QTreeWidget, QTableWidget {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                outline: 0;
            }
            
            QHeaderView::section {
                background-color: #424242;
                color: white;
                padding: 5px;
                border: none;
                border-right: 1px solid #555;
                border-bottom: 1px solid #555;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #333;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                background-color: #333;
            }
            
            QProgressBar::chunk {
                background-color: #1976D2;
                width: 10px;
                margin: 0.5px;
            }
            
            QTabWidget::pane {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                background: #2b2b2b;
            }
            
            QTabBar::tab {
                background: #424242;
                color: white;
                padding: 5px 10px;
                border: 1px solid #555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background: #2b2b2b;
                border-bottom: 1px solid #2b2b2b;
                margin-bottom: -1px;
            }
            
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            
            QMenuBar {
                background-color: #2b2b2b;
                color: white;
            }
            
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            
            QMenuBar::item:selected {
                background-color: #424242;
            }
            
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
            }
            
            QMenu::item:selected {
                background-color: #424242;
            }
            
            QStatusBar {
                background-color: #2b2b2b;
                color: #aaa;
                border-top: 1px solid #555;
            }
            
            QToolBar {
                background-color: #333;
                border-bottom: 1px solid #444;
                spacing: 2px;
                padding: 2px;
            }
            
            QToolBar::separator {
                background: #555;
                width: 1px;
                margin: 4px 2px;
            }
            
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
                margin: 0 1px;
                min-width: 80px;
                min-height: 28px;
                text-align: center;
            }
            
            QToolButton:hover {
                background-color: #444;
                border: 1px solid #555;
            }
            
            QToolButton:pressed {
                background-color: #555;
                border: 1px solid #666;
            }
            
            QToolButton:disabled {
                color: #666;
                background-color: transparent;
                border: 1px solid transparent;
            }
            
            QToolButton#primaryButton {
                background-color: #1976D2;
                font-weight: bold;
                color: white;
                min-width: 90px;
            }
            
            QToolButton#primaryButton:hover {
                background-color: #1E88E5;
                border-color: #42A5F5;
            }
            
            QToolButton#primaryButton:pressed {
                background-color: #1565C0;
            }
            
            QToolButton#successButton {
                background-color: #2E7D32;
                color: white;
                font-weight: bold;
                min-width: 120px;
            }
            
            QToolButton#successButton:hover {
                background-color: #388E3C;
                border-color: #66BB6A;
            }
            
            QToolButton#successButton:pressed {
                background-color: #1B5E20;
            }
            
            QToolButton#dangerButton {
                background-color: #C62828;
                color: white;
                font-weight: bold;
            }
            
            QToolButton#dangerButton:hover {
                background-color: #D32F2F;
                border-color: #EF5350;
            }
            
            QToolButton#dangerButton:pressed {
                background-color: #B71C1C;
            }
            
            QToolButton QMenu::indicator {
                width: 0px;
                height: 0px;
            }
        """
        
        # Apply styles to the parent if provided, otherwise apply to QApplication
        if self.parent is not None:
            self.parent.setStyleSheet(stylesheet)
        else:
            app = QApplication.instance()
            if app is not None:
                app.setStyleSheet(stylesheet)
    
    def create_button(self, parent, text, slot=None, tooltip=None, style='default', icon=None):
        """
        Create a styled QPushButton with enhanced visual feedback.
        
        Args:
            parent: Parent widget
            text (str): Button text
            slot (callable, optional): Slot to connect to the clicked signal
            tooltip (str, optional): Tooltip text
            style (str): Button style ('default', 'primary', 'success', 'danger')
            icon (QIcon, optional): Optional icon for the button
            
        Returns:
            QPushButton: The created button
        """
        button = QPushButton(text, parent)
        
        # Set button style
        if style == 'primary':
            button.setObjectName('primaryButton')
        elif style == 'success':
            button.setObjectName('successButton')
        elif style == 'danger':
            button.setObjectName('dangerButton')
            
        # Set icon if provided
        if icon is not None:
            button.setIcon(icon)
            button.setIconSize(QSize(16, 16))
            
        # Set tooltip if provided
        if tooltip:
            button.setToolTip(tooltip)
            button.setStatusTip(tooltip)
            
        # Connect slot if provided
        if slot is not None:
            button.clicked.connect(slot)
            
        return button
        
    def create_toolbar(self, parent, orientation=Qt.Orientation.Horizontal):
        """
        Create a styled toolbar with consistent spacing.
        
        Args:
            parent: Parent widget
            orientation: Qt.Orientation.Horizontal or Qt.Orientation.Vertical
            
        Returns:
            QWidget: A widget containing the toolbar with proper layout
        """
        container = QWidget(parent)
        if orientation == Qt.Orientation.Horizontal:
            layout = QHBoxLayout(container)
        else:
            layout = QVBoxLayout(container)
            
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        container.setLayout(layout)
        
        # Add a subtle background to the toolbar
        container.setStyleSheet("""
            QWidget#toolbar {
                background-color: #333;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        container.setObjectName("toolbar")
        
        return container, layout
    
    def create_label(self, text, title=False, align=Qt.AlignmentFlag.AlignLeft):
        """
        Create a styled QLabel.
        
        Args:
            text (str): Label text
            title (bool): Whether to use title style
            align (Qt.Alignment): Text alignment
            
        Returns:
            QLabel: The created label
        """
        label = QLabel(text, self.parent)
        if title:
            label.setObjectName("titleLabel")
        label.setAlignment(align)
        return label
    
    def create_horizontal_line(self):
        """
        Create a horizontal line widget.
        
        Returns:
            QFrame: A horizontal line widget
        """
        line = QFrame(self.parent)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #555;")
        return line
    
    def create_frame(self, parent, direction="vertical"):
        """
        Create a frame with the specified layout direction.
        
        Args:
            parent: Parent widget
            direction (str): Layout direction - 'vertical' or 'horizontal'
            
        Returns:
            tuple: (frame, layout) - The created frame and its layout
        """
        frame = QFrame(parent)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1)
        
        if direction.lower() == "vertical":
            layout = QVBoxLayout(frame)
        else:
            layout = QHBoxLayout(frame)
            
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        return frame, layout
    
    def create_file_list(self, parent):
        """
        Create a styled list widget for displaying loaded files.
        
        Args:
            parent: Parent widget
            
        Returns:
            QListWidget: The created list widget
        """
        file_list = QListWidget(parent)
        file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        file_list.setAlternatingRowColors(True)
        file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #333;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #1976D2;
                color: white;
            }
            QListWidget::item:alternate {
                background-color: #2a2a2a;
            }
            QScrollBar:vertical {
                border: none;
                background: #333;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555;
                min-height: 20px;
                border-radius: 5px;
            }
        """)
        return file_list
        
    def create_checkbox(self, parent, text, checked=False, tooltip=None):
        """
        Create a styled checkbox.
        
        Args:
            parent: Parent widget
            text (str): Checkbox text
            checked (bool): Initial checked state
            tooltip (str, optional): Tooltip text
            
        Returns:
            QCheckBox: The created checkbox
        """
        checkbox = QCheckBox(text, parent)
        checkbox.setChecked(checked)
        if tooltip:
            checkbox.setToolTip(tooltip)
            
        # Apply styling
        checkbox.setStyleSheet("""
            QCheckBox {
                color: #EEEEEE;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #555;
                border-radius: 3px;
                background: #333;
            }
            QCheckBox::indicator:checked {
                background: #1976D2;
                border: 1px solid #1976D2;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 1px solid #777;
            }
        """)
        return checkbox
        
    def create_double_spinbox(self, parent, minimum=0.0, maximum=100.0, value=0.0, 
                            step=1.0, decimals=2, tooltip=None):
        """
        Create a styled double spinbox.
        
        Args:
            parent: Parent widget
            minimum (float): Minimum value
            maximum (float): Maximum value
            value (float): Initial value
            step (float): Step size
            decimals (int): Number of decimal places
            tooltip (str, optional): Tooltip text
            
        Returns:
            QDoubleSpinBox: The created spinbox
        """
        spinbox = QDoubleSpinBox(parent)
        spinbox.setRange(minimum, maximum)
        spinbox.setValue(value)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(decimals)
        
        if tooltip:
            spinbox.setToolTip(tooltip)
            
        # Apply styling
        spinbox.setStyleSheet("""
            QDoubleSpinBox {
                padding: 2px 5px;
                min-width: 60px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 15px;
            }
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {
                width: 7px;
                height: 7px;
            }
        """)
        return spinbox

    def create_text_editor(self, parent=None):
        """Create and configure a QsciScintilla text editor for G-code."""
        from PyQt6.QtGui import QColor, QFont, QFontMetrics
        
        # Create the editor
        editor = QsciScintilla(parent)
        
        # Use Python lexer as a base (better than nothing)
        lexer = QsciLexerPython()
        lexer.setDefaultFont(QFont("Consolas", 10))
        
        # Set editor properties
        editor.setLexer(lexer)
        editor.setUtf8(True)
        editor.setAutoIndent(True)
        editor.setIndentationGuides(True)
        editor.setIndentationsUseTabs(False)
        editor.setIndentationWidth(4)
        editor.setTabWidth(4)
        editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor("#e8e8e8"))
        
        # Set margins
        font_metrics = QFontMetrics(QFont("Consolas", 9))
        editor.setMarginsFont(QFont("Consolas", 9))
        editor.setMarginWidth(0, font_metrics.horizontalAdvance("00000") + 6)
        editor.setMarginLineNumbers(0, True)
        editor.setMarginsBackgroundColor(QColor("#f0f0f0"))
        
        # Enable code folding
        editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle, 2)
        
        return editor
