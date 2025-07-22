"""
Translation strings for STL to G-Code v{version}.
"""

# List of available language codes
LANGUAGES = ["en", "it"]

# Translation strings organized by language
TRANSLATIONS = {
    "en": {
        # Application
        "app_title": "STL to G-Code v{version}",
        
        # Menu items
        "file_menu": {
            "title": "&File",
            "open_stl": "&Open STL...",
            "open_gcode": "Open &G-code...",
            "save_gcode": "&Save G-code...",
            "recent_files": "Recent Files",
            "exit": "E&xit"
        },
        "edit_menu": {
            "title": "&Edit",
            "settings": "&Settings..."
        },
        "view_menu": {
            "title": "&View",
            "show_log": "Show &Log",
            "language": "&Language"
        },
        "help_menu": {
            "title": "&Help",
            "documentation": "&Documentation...",
            "help": "&Help",
            "check_updates": "Check for &Updates...",
            "about": "&About...",
            "sponsor": "&Sponsor..."
        },
        
        # About text
        "about_title": "About",
        "app_name": "STL to G-Code",
        "version": "Version {version}",
        "github": "GitHub",
        "system_information": "System Information",
        "operating_system": "Operating System",
        "error_loading_system_info": "Error loading system information",
        "about_description": "This application is developed and maintained by a single developer.\nYour support helps keep the project alive and allows for new features and improvements.",
        "copyright": "(c) 2025 Nsfr750",
        "license": "Licensed under the GPLv3 License",

        # Sponsor dialog
        "support_title": "Support STL to G-Code",
        "support_project": "Support the Project",
        "support_project_header": "Support STL to G-Code",
        "support_project_description": "This application is developed and maintained by a single developer.\nYour support helps keep the project alive and allows for new features and improvements.",
        "support_on_patreon": "Support on Patreon",
        "donate_via_paypal": "Donate with PayPal",
        "copy_address": "Copy Address",
        "address_copied": "Address Copied",
        "address_copied_to_clipboard": "address copied to clipboard",
        "support_development": "Support Development",
        "support_app_name": "Support STL to G-Code",
        "support_message": "If you find this application useful, we invite you to support its development.\n\nYour support helps cover hosting costs and encourages further development.",
        "github_sponsors": "GitHub Sponsors",
        "paypal_donation": "PayPal Donation",
        "monero": "Monero",
        "scan_to_donate_xmr": "Scan to donate XMR",
        "qr_generation_failed": "QR code generation failed",
        "ways_to_support": "Ways to Support",
        "other_ways_to_help": "Other Ways to Help",
        "star_on_github": "Star the project on",
        "report_bugs": "Report bugs and suggest features",
        "share_with_others": "Share with others who might find it useful",
        "copied": "Copied!",
        "close": "Close",
        "donate_with_paypal": "Donate with PayPal",
        "copy_monero_address": "Copy Monero Address",

        # Log viewer
        "log_viewer": "Log Viewer",
        "filter_logs": "Filter Logs",
        "no_log_file": "No log file available.",
        "error_reading_log": "Error reading log file: {error}",
        "clear_logs": "Clear Logs",
        "confirm_clear_logs": "Are you sure you want to clear all logs? This action cannot be undone.",
        "save_logs": "Save Logs",
        "save_log_file": "Save Log File",
        "log_files": "Log Files (*.log);;All Files (*)",
        "logs_saved": "Logs successfully saved to: {path}",
        "failed_save_logs": "Failed to save log file: {error}",
        "log_level": "Log Level",
        "all_levels": "All Levels",
        "refresh": "Refresh",
        "select_log_file": "Select Log File",
        "no_logs_found": "No Logs Found",
        "log_level_filters": "Log Level Filters",
        "clear_log": "Clear Log",
        "save_as": "Save As",
        "no_logs_available": "No Logs Available",

        # G-code Editor
        "gcode_editor": {
            "no_issues": "No issues",
            "no_issues_found": "No issues found",
            "error_count": "{count} error" if "{count}" == "1" else "{count} errors",
            "warning_count": "{count} warning" if "{count}" == "1" else "{count} warnings",
            "info_count": "{count} info" if "{count}" == "1" else "{count} info",
            "issue_line": "{icon} Line {line}: {message}",
            "validation_error": "Validation Error",
            "validation_warning": "Validation Warning",
            "validation_info": "Information",
            "save_changes": "Save Changes",
            "discard_changes": "Discard Changes",
            "unsaved_changes": "You have unsaved changes. Would you like to save them?"
        },

        # G-code Validator Translations
        "validation.severity.info": "Info",
        "validation.severity.warning": "Warning",
        "validation.severity.error": "Error",
        "validation.severity.critical": "Critical",
        
        "validation.error.invalid_syntax": "Invalid G-code syntax",
        "validation.error.invalid_parameter": "Invalid parameter value: {param}",
        "validation.error.processing_command": "Error processing command {command}: {error}",
        "validation.error.invalid_tool": "Invalid tool number: T{tool}",
        "validation.error.invalid_tool_selection": "Invalid tool selection: {command}",
        "validation.error.negative_feedrate": "Feedrate cannot be negative",
        "validation.error.axis_out_of_bounds": "{axis} position {value} is out of bounds (0-{max_pos})",
        "validation.error.invalid_fan_speed": "Fan speed {speed} is outside valid range (0-255)",
        
        "validation.warning.feedrate_exceeds_max": "Feedrate {feedrate} exceeds maximum of {max_feedrate}",
        "validation.warning.temp_out_of_range": "Extruder temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_heated_bed": "Printer does not have a heated bed",
        "validation.warning.bed_temp_out_of_range": "Bed temperature {temp}°C is outside safe range ({min_temp}-{max_temp}°C)",
        "validation.warning.no_controllable_fan": "Printer does not have a controllable fan",
        "validation.warning.hotend_hot_fan_off": "Hotend is hot but part cooling fan is off",
        "validation.warning.hotend_hot_away_from_bed": "Hotend is hot but appears to be away from the print area",
        
        # Update checker
        "update_available": "Update Available",
        "new_version_available": "A new version of STL to G-Code is available!",
        "current_version": "Your version: {current_version}",
        "latest_version": "Latest version: {latest_version}",
        "download_update": "Download Update",
        "remind_me_later": "Remind Me Later",
        "skip_this_version": "Skip This Version",
        "checking_for_updates": "Checking for updates...",
        "up_to_date": "You are using the latest version of STL to G-Code.",
        "update_error": "Error checking for updates",
        "update_check_failed": "Failed to check for updates: {error}",
        "release_notes": "Release Notes",
        "download": "Download",
        "view_changes": "View Changes",
        "update_available_title": "Update Available",
    },
    "it": {
        # Application
        "app_title": "STL a G-Code v{version}",
        
        # Menu items
        "file_menu": {
            "title": "&File",
            "open_stl": "&Apri STL...",
            "open_gcode": "Apri &G-code...",
            "save_gcode": "&Salva G-code...",
            "recent_files": "File recenti",
            "exit": "E&sci"
        },
        "edit_menu": {
            "title": "&Modifica",
            "settings": "Impo&stazioni..."
        },
        "view_menu": {
            "title": "&Visualizza",
            "show_log": "Mostra &Log",
            "language": "&Lingua"
        },
        "help_menu": {
            "title": "&Aiuto",
            "documentation": "&Documentazione...",
            "help": "&Aiuto",
            "check_updates": "Controlla &Aggiornamenti...",
            "about": "&Informazioni...",
            "sponsor": "&Supporta il Progetto..."
        },
        
        # About dialog
        "about_title": "Informazioni",
        "app_name": "STL a G-Code",
        "version": "Versione {version}",
        "github": "GitHub",
        "system_information": "Informazioni di Sistema",
        "operating_system": "Sistema Operativo",
        "error_loading_system_info": "Errore nel caricamento delle informazioni di sistema",
        "about_description": "Questa applicazione è sviluppata e mantenuta da un singolo sviluppatore.\nIl tuo supporto aiuta a mantenere in vita il progetto e a sviluppare nuove funzionalità e miglioramenti.",
        "copyright": " 2025 Nsfr750",
        "license": "Distribuito con licenza GPLv3",
        
        # Sponsor dialog
        "support_title": "Supporta STL a G-Code",
        "support_project": "Supporta il Progetto",
        "support_project_header": "Supporta STL a G-Code",
        "support_project_description": "Questa applicazione è sviluppata e mantenuta da un singolo sviluppatore.\nIl tuo supporto aiuta a mantenere in vita il progetto e a sviluppare nuove funzionalità e miglioramenti.",
        "support_on_patreon": "Supporta su Patreon",
        "donate_via_paypal": "Dona con PayPal",
        "copy_address": "Copia Indirizzo",
        "address_copied": "Indirizzo Copiato",
        "address_copied_to_clipboard": "indirizzo copiato negli appunti",
        "support_development": "Supporta lo Sviluppo",
        "support_app_name": "Supporta STL a G-Code",
        "support_message": "Se trovi utile questa applicazione, ti invitiamo a supportarne lo sviluppo.\n\nIl tuo supporto aiuta a coprire i costi di hosting e incoraggia ulteriori sviluppi.",
        "github_sponsors": "GitHub Sponsors",
        "paypal_donation": "Donazione PayPal",
        "monero": "Monero",
        "scan_to_donate_xmr": "Scansiona per donare XMR",
        "qr_generation_failed": "Generazione codice QR fallita",
        "ways_to_support": "Modi per Supportare",
        "other_ways_to_help": "Altri Modi per Aiutare",
        "star_on_github": "Metti una stella al progetto su",
        "report_bugs": "Segnala bug e suggerisci funzionalità",
        "share_with_others": "Condividi con altri che potrebbero trovarlo utile",
        "copied": "Copiato!",
        "close": "Chiudi",
        "donate_with_paypal": "Dona con PayPal",
        "copy_monero_address": "Copia Indirizzo Monero",

        # Log viewer
        "log_viewer": "Visualizzatore Log",
        "filter_logs": "Filtra Log",
        "no_log_file": "Nessun file di log disponibile.",
        "error_reading_log": "Errore durante la lettura del file di log: {error}",
        "clear_logs": "Pulisci Log",
        "confirm_clear_logs": "Sei sicuro di voler cancellare tutti i log? Questa azione non può essere annullata.",
        "save_logs": "Salva Log",
        "save_log_file": "Salva File di Log",
        "log_files": "File di Log (*.log);;Tutti i File (*)",
        "logs_saved": "Log salvati con successo in: {path}",
        "failed_save_logs": "Impossibile salvare il file di log: {error}",
        "log_level": "Livello di Log",
        "all_levels": "Tutti i Livelli",
        "refresh": "Aggiorna",
        "select_log_file": "Seleziona File di Log",
        "no_logs_found": "Nessun Log Trovato",
        "log_level_filters": "Filtri Livello Log",
        "clear_log": "Pulisci Log",
        "save_as": "Salva come",
        "no_logs_available": "Nessun Log Disponibile",

        # G-code Editor
        "gcode_editor": {
            "no_issues": "Nessun problema",
            "no_issues_found": "Nessun problema trovato",
            "error_count": "{count} errore" if "{count}" == "1" else "{count} errori",
            "warning_count": "{count} avviso" if "{count}" == "1" else "{count} avvisi",
            "info_count": "{count} informazione" if "{count}" == "1" else "{count} informazioni",
            "issue_line": "{icon} Riga {line}: {message}",
            "validation_error": "Errore di convalida",
            "validation_warning": "Avviso di convalida",
            "validation_info": "Informazione",
            "save_changes": "Salva modifiche",
            "discard_changes": "Annulla modifiche",
            "unsaved_changes": "Hai delle modifiche non salvate. Vuoi salvarle?"
        },

        # G-code Validator Translations
        "validation.severity.info": "Informazione",
        "validation.severity.warning": "Avviso",
        "validation.severity.error": "Errore",
        "validation.severity.critical": "Critico",
        
        "validation.error.invalid_syntax": "Sintassi G-code non valida",
        "validation.error.invalid_parameter": "Valore parametro non valido: {param}",
        "validation.error.processing_command": "Errore durante l'elaborazione del comando {command}: {error}",
        "validation.error.invalid_tool": "Numero utensile non valido: T{tool}",
        "validation.error.invalid_tool_selection": "Selezione utensile non valida: {command}",
        "validation.error.negative_feedrate": "La velocità di avanzamento non può essere negativa",
        "validation.error.axis_out_of_bounds": "La posizione {axis} {value} è fuori dai limiti (0-{max_pos})",
        "validation.error.invalid_fan_speed": "La velocità della ventola {speed} è al di fuori dell'intervallo valido (0-255)",
        
        "validation.warning.feedrate_exceeds_max": "La velocità di avanzamento {feedrate} supera il massimo di {max_feedrate}",
        "validation.warning.temp_out_of_range": "La temperatura dell'estrusore {temp}°C è al di fuori dell'intervallo di sicurezza ({min_temp}-{max_temp}°C)",
        "validation.warning.no_heated_bed": "La stampante non ha un piano riscaldato",
        "validation.warning.bed_temp_out_of_range": "La temperatura del piano {temp}°C è al di fuori dell'intervallo di sicurezza ({min_temp}-{max_temp}°C)",
        "validation.warning.no_controllable_fan": "La stampante non ha una ventola controllabile",
        "validation.warning.hotend_hot_fan_off": "L'hotend è caldo ma la ventola di raffreddamento è spenta",
        "validation.warning.hotend_hot_away_from_bed": "L'hotend è caldo ma sembra essere lontano dall'area di stampa",
        
        # Update checker
        "update_available": "Aggiornamento Disponibile",
        "new_version_available": "È disponibile una nuova versione di STL a G-Code!",
        "current_version": "La tua versione: {current_version}",
        "latest_version": "Ultima versione: {latest_version}",
        "download_update": "Scarica Aggiornamento",
        "remind_me_later": "Ricordamelo più tardi",
        "skip_this_version": "Salta questa versione",
        "checking_for_updates": "Controllo aggiornamenti in corso...",
        "up_to_date": "Stai utilizzando l'ultima versione di STL a G-Code.",
        "update_error": "Errore durante il controllo degli aggiornamenti",
        "update_check_failed": "Impossibile controllare gli aggiornamenti: {error}",
        "release_notes": "Note di Rilascio",
        "download": "Scarica",
        "view_changes": "Visualizza Modifiche",
        "update_available_title": "Aggiornamento Disponibile",
    },
}


# Backward compatibility function
def t(key: str, lang_code: str = "en", **kwargs) -> str:
    """
    Get a translated string for the given key and language.

    Note: This is kept for backward compatibility. New code should use LanguageManager.

    Args:
        key: The translation key
        lang_code: Language code (default: 'en')
        **kwargs: Format arguments for the translation string

    Returns:
        str: The translated string or the key if not found
    """
    try:
        translation = TRANSLATIONS.get(lang_code, {}).get(
            key, TRANSLATIONS.get("en", {}).get(key, key)
        )
        if isinstance(translation, str) and kwargs:
            return translation.format(**kwargs)
        return translation
    except Exception as e:
        print(f"Translation error for key '{key}': {e}")
        return key
