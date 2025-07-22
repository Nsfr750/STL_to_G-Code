"""
Enhanced G-code editor with syntax highlighting and validation.
"""

from PyQt6.Qsci import QsciScintilla, QsciLexerCustom
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QToolBar, QTextEdit, QListWidget, QSplitter)
from typing import List, Dict, Optional
import re
import logging
from scripts.logger import get_logger

from .gcode_validator import GCodeValidator, ValidationIssue, ValidationSeverity, PrinterLimits
from .language_manager import LanguageManager

class GCodeLexer(QsciLexerCustom):
    """Custom lexer for G-code syntax highlighting."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define styles
        self.styles = {
            0: "default",
            1: "g_command",
            2: "m_command",
            3: "parameter",
            4: "comment",
            5: "error"
        }
        
        # Set default font
        font = QFont("Consolas", 10)
        self.setDefaultFont(font)
        
        # Set colors for styles
        self.setColor(QColor("#d4d4d4"), 0)  # Default
        self.setColor(QColor("#4ec9b0"), 1)   # G-command
        self.setColor(QColor("#c586c0"), 2)   # M-command
        self.setColor(QColor("#9cdcfe"), 3)   # Parameter
        self.setColor(QColor("#6a9955"), 4)   # Comment
        self.setColor(QColor("#f44747"), 5)   # Error
        
        # Set paper color
        self.setPaper(QColor("#1e1e1e"))
        
        # Compile regex patterns
        self.g_command = re.compile(r'\bG[0-9]+\b', re.IGNORECASE)
        self.m_command = re.compile(r'\bM[0-9]+\b', re.IGNORECASE)
        self.parameter = re.compile(r'[A-Z][-+]?[0-9]*\.?[0-9]*', re.IGNORECASE)
        self.comment = re.compile(r';.*$')
    
    def language(self):
        return "G-code"
    
    def description(self, style):
        return self.styles.get(style, "")
    
    def styleText(self, start, end):
        """Style the text in the editor."""
        if not self.editor():
            return
            
        # Get the text to style
        text = self.editor().text()[start:end]
        if not text:
            return
            
        # Initialize styling
        self.startStyling(start)
        
        # Split into lines
        lines = text.split('\n')
        position = 0
        
        for line in lines:
            if not line:
                position += 1  # For the newline
                continue
                
            # Default style for the whole line
            self.setStyling(len(line), 0)
            
            # Find and style G-commands
            for match in self.g_command.finditer(line):
                self.startStyling(start + match.start())
                self.setStyling(match.end() - match.start(), 1)
            
            # Find and style M-commands
            for match in self.m_command.finditer(line):
                self.startStyling(start + match.start())
                self.setStyling(match.end() - match.start(), 2)
            
            # Find and style parameters
            for match in self.parameter.finditer(line):
                param = match.group(0)
                if not (param.startswith(('G', 'g', 'M', 'm')) and param[1:].isdigit()):
                    self.startStyling(start + match.start())
                    self.setStyling(match.end() - match.start(), 3)
            
            # Find and style comments
            comment_match = self.comment.search(line)
            if comment_match:
                self.startStyling(start + comment_match.start())
                self.setStyling(len(line) - comment_match.start(), 4)
            
            position += len(line) + 1  # +1 for the newline


class GCodeEditor(QsciScintilla):
    """Enhanced G-code editor with syntax highlighting and validation."""
    
    # Signals
    validation_complete = pyqtSignal(list)  # List of ValidationIssue objects
    
    def __init__(self, parent=None, language_manager: Optional[LanguageManager] = None):
        super().__init__(parent)
        self.validator = GCodeValidator()
        self.issues = []
        self.language_manager = language_manager or LanguageManager()
        self._setup_editor()
        self._setup_validation()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect language manager signals."""
        if self.language_manager:
            self.language_manager.language_changed.connect(self.retranslate_ui)
    
    def retranslate_ui(self):
        """Retranslate UI elements on language change."""
        # This editor doesn't have many UI elements to retranslate
        pass
    
    def _setup_editor(self):
        """Set up the editor with syntax highlighting and basic settings."""
        # Set up the editor
        self.setUtf8(True)
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setIndentationWidth(4)
        self.setTabWidth(4)
        self.setTabIndents(True)
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#2a2d2e"))
        self.setMarginLineNumbers(1, True)
        self.setMarginWidth(1, "0000")
        self.setMarginsBackgroundColor(QColor("#252526"))
        self.setMarginsForegroundColor(QColor("#858585"))
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(False)
        self.setAutoCompletionShowSingle(True)
        
        # Set up lexer
        self.lexer = GCodeLexer(self)
        self.setLexer(self.lexer)
        
        # Set up indicators for errors and warnings
        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, 0)  # Error
        self.setIndicatorForegroundColor(QColor("#f44747"), 0)
        
        self.indicatorDefine(QsciScintilla.IndicatorStyle.SquiggleIndicator, 1)  # Warning
        self.setIndicatorForegroundColor(QColor("#ffcc00"), 1)
        
        # Connect text changed signal
        self.textChanged.connect(self._on_text_changed)
    
    def _setup_validation(self):
        """Set up validation timer and settings."""
        self.validation_timer = QTimer(self)
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_gcode)
        self.last_validation_pos = 0
        self.validation_delay = 1000  # ms
    
    def _on_text_changed(self):
        """Handle text changes and schedule validation."""
        # Clear existing indicators
        self.clear_indicators()
        
        # Restart the validation timer
        self.validation_timer.stop()
        self.validation_timer.start(self.validation_delay)
    
    def _validate_gcode(self):
        """Validate the G-code and update indicators."""
        gcode = self.text()
        if not gcode.strip():
            self.issues = []
            self.validation_complete.emit([])
            return
        
        # Run validation
        self.issues = self.validator.validate(gcode)
        
        # Update indicators
        self._update_indicators()
        
        # Emit signal with issues
        self.validation_complete.emit(self.issues)
    
    def _update_indicators(self):
        """Update the editor indicators based on validation issues."""
        for issue in self.issues:
            line = issue.line_number - 1  # Convert to 0-based
            if line < 0 or line >= self.lines():
                continue
                
            # Get the line text
            line_text = self.text(line)
            if not line_text:
                continue
                
            # Determine indicator style based on severity
            indicator = 0  # Default to error
            if issue.severity in (ValidationSeverity.WARNING, ValidationSeverity.INFO):
                indicator = 1  # Warning
            
            # Highlight the entire line
            start_pos = self.positionFromLineIndex(line, 0)
            end_pos = self.positionFromLineIndex(line, len(line_text))
            
            # Apply the indicator
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator)
            self.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos - start_pos)
    
    def clear_indicators(self):
        """Clear all error/warning indicators."""
        for indicator in [0, 1]:  # Error and warning indicators
            self.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, indicator)
            self.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, len(self.text()))
    
    def set_printer_limits(self, limits: PrinterLimits):
        """Update the printer limits used for validation."""
        self.validator = GCodeValidator(limits)
        self._validate_gcode()  # Revalidate with new limits
    
    def get_issues(self) -> List[ValidationIssue]:
        """Get the list of validation issues."""
        return self.issues


class GCodeEditorWidget(QWidget):
    """Widget containing the G-code editor with validation results."""
    
    def __init__(self, parent=None, language_manager: Optional[LanguageManager] = None):
        super().__init__(parent)
        self.language_manager = language_manager or LanguageManager()
        self._setup_ui()
        self._setup_connections()
        self.retranslate_ui()
    
    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout(self)
        
        # Splitter for editor and issues panel
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Create editor
        self.editor = GCodeEditor(language_manager=self.language_manager)
        
        # Create issues panel
        self.issues_panel = QWidget()
        issues_layout = QVBoxLayout(self.issues_panel)
        
        # Issues toolbar
        toolbar = QToolBar()
        self.issues_label = QLabel()
        toolbar.addWidget(self.issues_label)
        
        # Issues list
        self.issues_list = QListWidget()
        self.issues_list.setVisible(False)
        
        # Add to layout
        issues_layout.addWidget(toolbar)
        issues_layout.addWidget(self.issues_list)
        
        # Add to splitter
        splitter.addWidget(self.editor)
        splitter.addWidget(self.issues_panel)
        splitter.setSizes([self.height() * 2 // 3, self.height() // 3])
        
        layout.addWidget(splitter)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.editor.validation_complete.connect(self._on_validation_complete)
        if self.language_manager:
            self.language_manager.language_changed.connect(self.retranslate_ui)
    
    def retranslate_ui(self):
        """Retranslate UI elements when language changes."""
        if not self.issues_list.count():
            self.issues_label.setText(
                self.language_manager.get_translation("gcode_editor.no_issues")
            )
    
    def _on_validation_complete(self, issues):
        """Handle validation completion."""
        self.issues_list.clear()
        
        if not issues:
            self.issues_label.setText(
                self.language_manager.get_translation("gcode_editor.no_issues_found")
            )
            self.issues_list.setVisible(False)
            return
        
        # Update issues label
        error_count = sum(1 for i in issues if i.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL))
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)
        
        status = []
        if error_count:
            status.append(
                self.language_manager.get_translation(
                    "gcode_editor.error_count", 
                    count=error_count
                )
            )
        if warning_count:
            status.append(
                self.language_manager.get_translation(
                    "gcode_editor.warning_count", 
                    count=warning_count
                )
            )
        if info_count:
            status.append(
                self.language_manager.get_translation(
                    "gcode_editor.info_count", 
                    count=info_count
                )
            )
        
        if status:
            self.issues_label.setText(" • ".join(status))
        else:
            self.issues_label.setText(
                self.language_manager.get_translation("gcode_editor.no_issues")
            )
        
        # Add issues to list
        for issue in issues:
            icon = "🛑"  # Default icon for errors
            if issue.severity == ValidationSeverity.WARNING:
                icon = "⚠️"
            elif issue.severity == ValidationSeverity.INFO:
                icon = "ℹ️"
                
            self.issues_list.addItem(
                self.language_manager.get_translation(
                    "gcode_editor.issue_line",
                    icon=icon,
                    line=issue.line_number,
                    message=issue.message
                )
            )
        
        self.issues_list.setVisible(True)
    
    def set_text(self, text: str):
        """Set the editor text."""
        self.editor.setText(text)
    
    def get_text(self) -> str:
        """Get the editor text."""
        return self.editor.text()
    
    def set_printer_limits(self, limits):
        """Set the printer limits for validation."""
        self.editor.set_printer_limits(limits)
    
    def get_issues(self) -> List[ValidationIssue]:
        """Get the list of validation issues."""
        return self.editor.get_issues()
