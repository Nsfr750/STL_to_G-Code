"""
Language management module for STL to G-Code Converter.

This module provides the LanguageManager class which handles application
internationalization and translation management.
"""

from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QSettings
import logging

# Configure logging
logger = logging.getLogger(__name__)

class LanguageManager(QObject):
    """
    Manages application language settings and translations.
    
    This class handles loading translations, changing languages at runtime,
    and providing translated strings to the application.
    """

    # Signal emitted when language changes
    language_changed = pyqtSignal(str)  # language_code

    def __init__(self, default_lang: str = "en"):
        """
        Initialize the language manager.

        Args:
            default_lang: Default language code (e.g., 'en', 'it')
        """
        super().__init__()
        logger.debug("Initializing LanguageManager...")
        
        # Initialize settings
        self.settings = QSettings("STL_to_G-Code", "STL_to_G-Code")
        logger.debug("Settings file: %s", self.settings.fileName())
        
        # Load current language from settings or use default
        self._current_lang = self.settings.value("language", default_lang)
        logger.debug("Current language from settings: %s", self._current_lang)
        
        # Initialize translations dictionary
        self._translations = {}
        self._available_languages = {}
        
        # Load translations
        self._load_translations()
        
        # Set up available languages based on what translations are available
        self._setup_available_languages()
        
        # If current language is not available, fall back to default
        if self._current_lang not in self._available_languages:
            logger.warning(
                "Language '%s' not available, falling back to '%s'",
                self._current_lang, default_lang
            )
            self._current_lang = default_lang
            
        logger.info("LanguageManager initialized with language: %s", self._current_lang)

    def _setup_available_languages(self):
        """Set up the available languages based on loaded translations."""
        self._available_languages = {
            "en": "English",
            "it": "Italiano",
            # Add more languages here as they become available
        }
        
        # Only include languages that have translations loaded
        available_codes = set(self._translations.keys())
        self._available_languages = {
            code: name 
            for code, name in self._available_languages.items()
            if code in available_codes
        }

    @property
    def current_language(self) -> str:
        """
        Get the current language code.
        
        Returns:
            str: Current language code (e.g., 'en', 'it')
        """
        return self._current_lang

    @property
    def available_languages(self) -> Dict[str, str]:
        """
        Get a dictionary of available language codes and their display names.
        
        Returns:
            Dict[str, str]: Dictionary mapping language codes to display names
        """
        return self._available_languages.copy()

    def _load_translations(self):
        """Load translations from the translations module."""
        try:
            from scripts.translations import TRANSLATIONS
            self._translations = TRANSLATIONS
            logger.debug("Loaded translations for languages: %s", 
                        ", ".join(TRANSLATIONS.keys()))
        except ImportError as e:
            logger.error("Failed to load translations: %s", e)
            self._translations = {"en": {}}  # Fallback to empty English translations

    def set_language(self, lang_code: str) -> bool:
        """
        Set the application language.

        Args:
            lang_code: Language code to set (e.g., 'en', 'it')

        Returns:
            bool: True if language was changed, False otherwise
        """
        if lang_code not in self._available_languages:
            logger.warning("Attempted to set unsupported language: %s", lang_code)
            return False

        if lang_code != self._current_lang:
            logger.info("Changing language from %s to %s", 
                      self._current_lang, lang_code)
            self._current_lang = lang_code
            self.settings.setValue("language", lang_code)
            self.language_changed.emit(lang_code)
            return True
            
        return False

    def translate(self, key: str, **kwargs) -> str:
        """
        Get a translated string for the given key.

        Args:
            key: Translation key (can contain dots for nested keys, 
                 e.g., 'menu.file.open')
            **kwargs: Format arguments for the translation string

        Returns:
            str: Translated string or the key if not found
        """
        if not key:
            return ""
            
        try:
            # Try to get translation for current language
            lang_dict = self._translations.get(self._current_lang, {})
            
            # Handle nested keys (e.g., 'menu.file.open')
            parts = key.split('.')
            result = lang_dict
            for part in parts:
                if not isinstance(result, dict):
                    result = None
                    break
                result = result.get(part)
            
            # If not found in current language, try English as fallback
            if result is None and self._current_lang != 'en':
                en_dict = self._translations.get('en', {})
                result = en_dict
                for part in parts:
                    if not isinstance(result, dict):
                        result = None
                        break
                    result = result.get(part)
                
                if result is not None:
                    # Only log missing translations in non-English languages
                    logger.debug("Using English fallback for key: %s", key)
            
            # If still not found, return the key and log a warning
            if result is None:
                # Only log a warning for non-debug keys to avoid log spam
                if not key.startswith('debug.') and not key.startswith('tooltips.'):
                    logger.warning("Translation key not found: %s (lang: %s)", 
                                key, self._current_lang)
                return key
                
            # Format the string with any provided arguments
            try:
                if kwargs:
                    if isinstance(result, str):
                        return result.format(**kwargs)
                    elif isinstance(result, (list, tuple)):
                        return [item.format(**kwargs) if isinstance(item, str) else str(item) 
                               for item in result]
                    else:
                        return str(result)
                return result
                
            except (KeyError, ValueError) as e:
                logger.warning("Error formatting translation for key '%s': %s", key, e)
                return key
                
        except Exception as e:
            logger.error("Error in translate('%s'): %s", key, e, exc_info=True)
            return key
